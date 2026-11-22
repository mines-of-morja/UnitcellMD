# Psi4 for layer-0 reference calculations (docs/research/forcefield-strategy.md, QM method).
# Validation only, like tools/oracle: nothing in the components uses it.
#   docker build -t ucmd-psi4:1.9.1 tools/qm
#   docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -e USER=psi4 -v "$PWD:/work" -w /work ucmd-psi4:1.9.1 psi4 input.dat
FROM condaforge/miniforge3:24.11.3-0
RUN mamba install -y -c conda-forge psi4=1.9.1 "libint=2.9.*" "libxc-c=6.*" python=3.12 numpy && mamba clean -afy
ENV PSI_SCRATCH=/tmp OMP_NUM_THREADS=4
CMD ["psi4", "--version"]
