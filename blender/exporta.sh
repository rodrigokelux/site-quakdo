#!/bin/bash
# Passa as imagens do Blender para o site, em WebP com transparência: o filme e o elenco.
# FILME=<pasta> escolhe a pasta do filme dentro de blender/saida (por omissão, "filme").
cd "$(dirname "$0")/.."
shopt -s nullglob
mkdir -p public/filme public/patos
for f in blender/saida/${FILME:-filme}/[0-9]*.png; do
  n=$(basename "$f" .png)
  [ -f "public/filme/$n.webp" ] && [ "public/filme/$n.webp" -nt "$f" ] && continue
  ffmpeg -y -loglevel error -i "$f" -c:v libwebp -pix_fmt yuva420p -quality 84 "public/filme/$n.webp"
done
# Elenco: fica só o pato (o chão e a sombra saem; a sombra é dada pelo CSS do site).
for f in blender/saida/elenco/*.png; do
  n=$(basename "$f" .png)
  [ -f "public/patos/$n.webp" ] && [ "public/patos/$n.webp" -nt "$f" ] && continue
  ffmpeg -y -loglevel error -i "$f" -vf "format=rgba,lut=a='if(lt(val,225),0,val)',crop=iw*0.9:ih*0.86:iw*0.05:ih*0.09,scale=760:-1" -c:v libwebp -quality 90 "public/patos/$n.webp"
done
echo "filme: $(ls public/filme | wc -l) imagens; patos: $(ls public/patos | wc -l)"
