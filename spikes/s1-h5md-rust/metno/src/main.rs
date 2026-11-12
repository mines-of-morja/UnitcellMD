//! Spike S1: write an H5MD 1.1 trajectory (spec/trajectory-h5md.md) with hdf5-metno and a
//! statically linked, bundled HDF5. Throwaway code; the outcome is recorded in ADR 0004.
//!
//! usage: s1-h5md-metno <out.h5> <n_atoms> <n_frames>
//! Positions follow a deterministic formula so that readers can check every value:
//!   x = i % 100 * 0.05 + 1e-3 * frame,  y = (i / 100) % 100 * 0.05,  z = i / 10000 * 0.05 + 2e-3 * frame

use hdf5::types::VarLenUnicode;
use hdf5::{Dataset, File, Group};
use ndarray::{Array2, Array3, s};
use std::time::Instant;

type Res<T> = Result<T, Box<dyn std::error::Error>>;

fn text(s: &str) -> Res<VarLenUnicode> {
    Ok(s.parse::<VarLenUnicode>()?)
}

fn attr_str(g: &Group, name: &str, value: &str) -> Res<()> {
    g.new_attr::<VarLenUnicode>().create(name)?.write_scalar(&text(value)?)?;
    Ok(())
}

fn unit(d: &Dataset, value: &str) -> Res<()> {
    d.new_attr::<VarLenUnicode>().create("unit")?.write_scalar(&text(value)?)?;
    Ok(())
}

/// Time-dependent H5MD element: step (i64), time (f64, ps) and a resizable value dataset.
struct Element {
    step: Dataset,
    time: Dataset,
    value: Dataset,
}

fn element(parent: &Group, name: &str, frame_shape: &[usize], unit_name: &str) -> Res<Element> {
    let g = parent.create_group(name)?;
    let step = g.new_dataset::<i64>().chunk(1024).shape(0..).create("step")?;
    let time = g.new_dataset::<f64>().chunk(1024).shape(0..).create("time")?;
    unit(&time, "ps")?;
    let value = match frame_shape {
        [] => g.new_dataset::<f64>().chunk(1024).shape(0..).create("value")?,
        [a, b] => g.new_dataset::<f64>().chunk((1, *a, *b)).shape((0.., *a, *b)).create("value")?,
        _ => return Err("unsupported frame shape".into()),
    };
    unit(&value, unit_name)?;
    Ok(Element { step, time, value })
}

fn system_json(n_atoms: usize, box_nm: f64) -> String {
    format!(
        concat!(
            r#"{{"format":"ucmd-system","spec_version":"0.1.0","name":"spike-s1","#,
            r#""units":{{"length":"nm","time":"ps","mass":"amu","energy":"kJ/mol","charge":"e","temperature":"K","angle":"deg"}},"#,
            r#""periodicity":[true,true,true],"cell_nm":[[{b},0,0],[{t},{b},0],[0,0,{b}]],"#,
            r#""molecule_types":{{"Ar":{{"formal_charge_e":0,"atoms":[{{"name":"Ar","element":"Ar","mass_amu":39.948}}],"bonds":[]}}}},"#,
            r#""components":[{{"molecule_type":"Ar","count":{n}}}],"atom_count":{n},"#,
            r#""provenance":{{"created_by":"spike S1","created_utc":"2026-11-12T00:00:00Z"}}}}"#
        ),
        b = box_nm,
        t = box_nm * 0.25,
        n = n_atoms
    )
}

fn main() -> Res<()> {
    let args: Vec<String> = std::env::args().collect();
    let path = &args[1];
    let n: usize = args[2].parse()?;
    let frames: usize = args[3].parse()?;
    let box_nm = 5.0;
    let started = Instant::now();

    let file = File::create(path)?;
    let h5md = file.create_group("h5md")?;
    h5md.new_attr::<i32>().shape(2).create("version")?.write(&[1, 1])?;
    attr_str(&h5md.create_group("author")?, "name", "anonymous")?;
    let creator = h5md.create_group("creator")?;
    attr_str(&creator, "name", "ucmd-spike-s1")?;
    attr_str(&creator, "version", "0.0.0")?;
    let modules = h5md.create_group("modules")?;
    modules.create_group("units")?.new_attr::<i32>().shape(2).create("version")?.write(&[1, 0])?;

    let all = file.create_group("particles")?.create_group("all")?;
    let boxg = all.create_group("box")?;
    boxg.new_attr::<i32>().create("dimension")?.write_scalar(&3)?;
    let periodic = [text("periodic")?, text("periodic")?, text("periodic")?];
    boxg.new_attr::<VarLenUnicode>().shape(3).create("boundary")?.write(&periodic)?;
    let edges = element(&boxg, "edges", &[3, 3], "nm")?;
    let position = element(&all, "position", &[n, 3], "nm")?;
    let mass = all.new_dataset::<f64>().shape(n).create("mass")?;
    mass.write(&vec![39.948; n])?;
    unit(&mass, "amu")?;
    all.new_dataset::<i32>().shape(n).create("species")?.write(&vec![18; n])?;
    let molecule_index: Vec<i64> = (0..n as i64).collect();
    all.new_dataset::<i64>().shape(n).create("molecule_index")?.write(&molecule_index)?;

    let obs = file.create_group("observables")?;
    let epot = element(&obs, "potential_energy", &[], "kJ mol-1")?;

    let ucmd = file.create_group("parameters")?.create_group("ucmd")?;
    attr_str(&ucmd, "spec_version", "0.1.0")?;
    attr_str(&ucmd, "positions", "unwrapped")?;
    ucmd.new_dataset::<VarLenUnicode>()
        .create("system_json")?
        .write_scalar(&text(&system_json(n, box_nm))?)?;
    ucmd.new_dataset::<VarLenUnicode>()
        .create("run_config_toml")?
        .write_scalar(&text("spec_version = \"0.1.0\"\n")?)?;

    let mut frame = Array2::<f64>::zeros((n, 3));
    let mut cell = Array2::<f64>::zeros((3, 3));
    cell[[0, 0]] = box_nm;
    cell[[1, 0]] = 0.25 * box_nm; // triclinic tilt b_x: checks the row orientation in readers
    cell[[1, 1]] = box_nm;
    cell[[2, 2]] = box_nm;
    let setup = started.elapsed();
    let writing = Instant::now();
    for k in 0..frames {
        for i in 0..n {
            frame[[i, 0]] = (i % 100) as f64 * 0.05 + 1e-3 * k as f64;
            frame[[i, 1]] = ((i / 100) % 100) as f64 * 0.05;
            frame[[i, 2]] = (i / 10000) as f64 * 0.05 + 2e-3 * k as f64;
        }
        for el in [&position, &edges, &epot] {
            el.step.resize(k + 1)?;
            el.step.write_slice(&[10 * k as i64], k..k + 1)?;
            el.time.resize(k + 1)?;
            el.time.write_slice(&[0.02 * k as f64], k..k + 1)?;
        }
        position.value.resize((k + 1, n, 3))?;
        position.value.write_slice(&frame, s![k, .., ..])?;
        edges.value.resize((k + 1, 3, 3))?;
        edges.value.write_slice(&cell, s![k, .., ..])?;
        epot.value.resize(k + 1)?;
        epot.value.write_slice(&[-1000.0 - k as f64], k..k + 1)?;
    }
    file.flush()?;
    let write_time = writing.elapsed();
    drop(file);
    let bytes = std::fs::metadata(path)?.len();
    let mb = (frames * n * 3 * 8) as f64 / 1e6;
    println!(
        "{{\"atoms\":{n},\"frames\":{frames},\"setup_s\":{:.3},\"write_s\":{:.3},\"payload_MB\":{mb:.1},\"file_MB\":{:.1},\"MB_per_s\":{:.0}}}",
        setup.as_secs_f64(),
        write_time.as_secs_f64(),
        bytes as f64 / 1e6,
        mb / write_time.as_secs_f64()
    );
    let _unused: Option<Array3<f64>> = None;
    Ok(())
}
