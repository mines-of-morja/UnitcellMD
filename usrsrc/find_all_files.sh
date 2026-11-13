find . -type f \( \
  -name "*.xyz" -o \
  -name "*.h5" -o \
  -name "*.h5md" -o \
  -name "*.tsv" -o \
  -name "*.ucchk" \
\) | head -100