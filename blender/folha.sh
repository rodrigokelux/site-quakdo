#!/bin/bash
# Junta as imagens de uma pasta numa folha de contacto sobre branco: blender/folha.sh <pasta> [colunas]
d="$1"; cols="${2:-4}"; ins=""; n=0
for f in "$d"/[0-9]*.png; do ins="$ins -i $f"; n=$((n+1)); done
rows=$(( (n + cols - 1) / cols )); fc=""
for i in $(seq 0 $((n-1))); do fc="$fc[$i]"; done
ffmpeg -y -loglevel error $ins -filter_complex "${fc}xstack=grid=${cols}x${rows}:fill=white[g];[g]split[a][b];[a]drawbox=c=white:t=fill[w];[w][b]overlay,scale=1600:-1" -frames:v 1 "$d/folha.jpg"
