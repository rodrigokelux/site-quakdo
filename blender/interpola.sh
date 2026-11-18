#!/bin/bash
# Passa o filme de 100 imagens a um vídeo para scroll: assenta cada imagem sobre o fundo azul (o mesmo do site),
# cria as imagens intermédias por interpolação de movimento (100 -> ~300) e codifica em H.264 só com imagens-chave,
# para o browser saltar para qualquer ponto sem esperar. Escreve public/filme.mp4.
cd "$(dirname "$0")/.."
ENTRADA=blender/saida/${FILME:-filme}
FATOR=${FATOR:-3}
TMP=blender/saida/interpolado
mkdir -p "$TMP"
# O fundo: azul da marca, um pouco mais claro atrás da obra, igual ao azul liso do site nas bordas.
ffmpeg -y -loglevel error -f lavfi -i "color=c=black:s=1920x1080,format=rgb24" -frames:v 1 -vf "geq=r='45+16*max(0\,1-hypot((X-0.66*W)/(0.55*W)\,(Y-0.48*H)/(0.7*H)))^1.6':g='85+19*max(0\,1-hypot((X-0.66*W)/(0.55*W)\,(Y-0.48*H)/(0.7*H)))^1.6':b='180+21*max(0\,1-hypot((X-0.66*W)/(0.55*W)\,(Y-0.48*H)/(0.7*H)))^1.6'" "$TMP/fundo.png"
ffmpeg -y -loglevel error -framerate 10 -start_number 0 -i "$ENTRADA/%03d.png" -loop 1 -i "$TMP/fundo.png" \
  -filter_complex "[1][0]scale2ref[f][v];[f][v]overlay=shortest=1:format=auto,format=yuv444p,minterpolate=fps=$((10 * FATOR)):mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=1600:-2:flags=lanczos,format=yuv420p" \
  -c:v libx264 -preset slow -crf 19 -g 1 -tune animation -movflags +faststart -an "$TMP/filme.mp4"
mv -f "$TMP/filme.mp4" public/filme.mp4
echo "vídeo: $(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 public/filme.mp4) imagens, $(du -h public/filme.mp4 | cut -f1)"
