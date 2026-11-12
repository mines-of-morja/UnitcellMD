//! Spike S4: minimal i-PI server (spec/force-provider.md §5), std only. Throwaway; see ADR 0007.
//!
//! usage: s4-ipi-server <socket-name> <input.bin> <repeats> <out.json>
//! input.bin (little endian): cell rows a, b, c in nm (9 f64), N (u64), positions in nm (3N f64).
//! Listens on /tmp/ipi_<socket-name>, evaluates the configuration `repeats` times through the
//! client, prints energy (kJ/mol), forces (kJ mol-1 nm-1), virial (kJ/mol) and timings as JSON.

use std::io::{self, BufReader, BufWriter, Read, Write};
use std::os::unix::net::{UnixListener, UnixStream};
use std::time::Instant;

const BOHR_NM: f64 = 0.0529177210903; // spec/units.md §2
const HARTREE_KJMOL: f64 = 2625.4996394798254;

struct Link {
    rx: BufReader<UnixStream>,
    tx: BufWriter<UnixStream>,
}

impl Link {
    fn send_msg(&mut self, msg: &str) -> io::Result<()> {
        let mut header = [b' '; 12];
        header[..msg.len()].copy_from_slice(msg.as_bytes());
        self.tx.write_all(&header)
    }
    fn recv_msg(&mut self) -> io::Result<String> {
        let mut header = [0u8; 12];
        self.rx.read_exact(&mut header)?;
        Ok(String::from_utf8_lossy(&header).trim().to_string())
    }
    fn send_f64(&mut self, values: &[f64]) -> io::Result<()> {
        let mut bytes = Vec::with_capacity(8 * values.len());
        for v in values {
            bytes.extend_from_slice(&v.to_le_bytes());
        }
        self.tx.write_all(&bytes)
    }
    fn send_i32(&mut self, v: i32) -> io::Result<()> {
        self.tx.write_all(&v.to_le_bytes())
    }
    fn recv_f64(&mut self, n: usize) -> io::Result<Vec<f64>> {
        let mut bytes = vec![0u8; 8 * n];
        self.rx.read_exact(&mut bytes)?;
        Ok(bytes.chunks_exact(8).map(|c| f64::from_le_bytes(c.try_into().unwrap())).collect())
    }
    fn recv_i32(&mut self) -> io::Result<i32> {
        let mut b = [0u8; 4];
        self.rx.read_exact(&mut b)?;
        Ok(i32::from_le_bytes(b))
    }
}

/// Inverse of a 3x3 matrix given as rows.
fn inverse(m: &[[f64; 3]; 3]) -> [[f64; 3]; 3] {
    let c = |i: usize, j: usize| m[i % 3][j % 3];
    let det = m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
    let mut inv = [[0.0; 3]; 3];
    for i in 0..3 {
        for j in 0..3 {
            // cofactor transpose
            inv[j][i] = (c(i + 1, j + 1) * c(i + 2, j + 2) - c(i + 1, j + 2) * c(i + 2, j + 1)) / det;
        }
    }
    inv
}

struct Evaluation {
    energy_kjmol: f64,
    forces: Vec<f64>,
    virial: [[f64; 3]; 3],
    extra: Vec<u8>,
}

fn evaluate(link: &mut Link, cell_nm: &[[f64; 3]; 3], positions_nm: &[f64]) -> io::Result<Evaluation> {
    link.send_msg("STATUS")?;
    link.tx.flush()?;
    let mut status = link.recv_msg()?;
    if status == "NEEDINIT" {
        link.send_msg("INIT")?;
        link.send_i32(0)?; // bead index
        link.send_i32(1)?;
        link.tx.write_all(&[0u8])?;
        link.send_msg("STATUS")?;
        link.tx.flush()?;
        status = link.recv_msg()?;
    }
    assert_eq!(status, "READY", "client not ready");

    // Wire convention (matches ASE's server): h = cell^T (lattice vectors as columns), row-major,
    // in bohr; then inverse(cell) row-major in 1/bohr; then N and positions in bohr.
    let cell_bohr: [[f64; 3]; 3] = std::array::from_fn(|i| std::array::from_fn(|j| cell_nm[i][j] / BOHR_NM));
    let h: Vec<f64> = (0..3).flat_map(|i| (0..3).map(move |j| cell_bohr[j][i])).collect();
    let inv = inverse(&cell_bohr);
    let ih: Vec<f64> = inv.iter().flatten().copied().collect();
    link.send_msg("POSDATA")?;
    link.send_f64(&h)?;
    link.send_f64(&ih)?;
    link.send_i32((positions_nm.len() / 3) as i32)?;
    let pos_bohr: Vec<f64> = positions_nm.iter().map(|x| x / BOHR_NM).collect();
    link.send_f64(&pos_bohr)?;
    link.send_msg("STATUS")?;
    link.tx.flush()?;
    let status = link.recv_msg()?;
    assert_eq!(status, "HAVEDATA", "client has no data");

    link.send_msg("GETFORCE")?;
    link.tx.flush()?;
    let reply = link.recv_msg()?;
    assert_eq!(reply, "FORCEREADY");
    let energy = link.recv_f64(1)?[0] * HARTREE_KJMOL;
    let n = link.recv_i32()? as usize;
    let forces: Vec<f64> = link.recv_f64(3 * n)?.into_iter().map(|f| f * HARTREE_KJMOL / BOHR_NM).collect();
    let m = link.recv_f64(9)?; // the client sends virial^T row-major
    let virial: [[f64; 3]; 3] = std::array::from_fn(|i| std::array::from_fn(|j| m[3 * j + i] * HARTREE_KJMOL));
    let n_extra = link.recv_i32()? as usize;
    let mut extra = vec![0u8; n_extra];
    link.rx.read_exact(&mut extra)?;
    Ok(Evaluation { energy_kjmol: energy, forces, virial, extra })
}

fn main() -> io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let socket = format!("/tmp/ipi_{}", args[1]);
    let input = std::fs::read(&args[2])?;
    let repeats: usize = args[3].parse().unwrap();
    let f = |k: usize| f64::from_le_bytes(input[8 * k..8 * k + 8].try_into().unwrap());
    let cell: [[f64; 3]; 3] = std::array::from_fn(|i| std::array::from_fn(|j| f(3 * i + j)));
    let n = u64::from_le_bytes(input[72..80].try_into().unwrap()) as usize;
    let positions: Vec<f64> = (0..3 * n).map(|k| f(10 + k)).collect();

    let _ = std::fs::remove_file(&socket);
    let listener = UnixListener::bind(&socket)?;
    let (stream, _) = listener.accept()?;
    let mut link = Link { rx: BufReader::new(stream.try_clone()?), tx: BufWriter::new(stream) };

    let first = evaluate(&mut link, &cell, &positions)?;
    let t0 = Instant::now();
    for _ in 1..repeats {
        evaluate(&mut link, &cell, &positions)?;
    }
    let per_step_ms = if repeats > 1 { t0.elapsed().as_secs_f64() * 1e3 / (repeats - 1) as f64 } else { 0.0 };
    link.send_msg("EXIT")?;
    link.tx.flush()?;
    let _ = std::fs::remove_file(&socket);

    let forces: Vec<String> = first.forces.iter().map(|v| format!("{v:e}")).collect();
    let virial: Vec<String> = first.virial.iter().map(|r| format!("[{:e},{:e},{:e}]", r[0], r[1], r[2])).collect();
    let json = format!(
        "{{\"energy_kjmol\":{:e},\"virial_kjmol\":[{}],\"extra_bytes\":{},\"per_step_ms\":{per_step_ms:.4},\"repeats\":{repeats},\"forces\":[{}]}}",
        first.energy_kjmol,
        virial.join(","),
        first.extra.len(),
        forces.join(",")
    );
    std::fs::write(&args[4], json)?;
    Ok(())
}
