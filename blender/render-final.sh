#!/bin/bash
# O render final: o filme em Full HD, em três passagens (uma imagem em cada 10, as do meio, e o resto), depois o elenco,
# e por fim a interpolação para ~300 imagens (scroll como um vídeo). As imagens vão sendo exportadas para o site.
cd "$(dirname "$0")/.."
B="/c/Program Files/Blender Foundation/Blender 5.3/blender.exe"
N=100; LARG=1920; AMOSTRAS=12
for idx in "$(seq 0 10 $((N - 1)) | tr '\n' ' ') $((N - 1))" "$(seq 5 10 $((N - 1)) | tr '\n' ' ')" ""; do
  "$B" -b -P "$PWD/blender/cena.py" -- "$PWD/blender/saida/filme" $LARG $AMOSTRAS $N $idx 2>&1 | grep -E "Error|Traceback"
  bash blender/exporta.sh
done
rm -f blender/saida/elenco/*.png
"$B" -b -P "$PWD/blender/elenco.py" -- "$PWD/blender/saida/elenco" 1000 40 2>&1 | grep -E "Error|Traceback"
bash blender/exporta.sh
bash blender/interpola.sh
echo FIM
