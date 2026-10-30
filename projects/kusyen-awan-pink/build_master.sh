#!/bin/bash
S=/tmp/claude-0/-home-user-tiktok-edit/e13a842d-03d7-5b65-8ccb-553016c42c9a/scratchpad
cd $S/work78
ffmpeg -nostdin -v error -y -i ../dl77/input.bin -map 0:a:0 -ac 1 -ar 16000 audio_a.wav
ffmpeg -nostdin -v error -y -i ../dl78/input.bin -map 0:a:0 -ac 1 -ar 16000 audio_b.wav
(cd $S/scripts && timeout 1500 python3 -I transcribe.py $S/work78/audio_a.wav $S/work78/tr_a.json > $S/work78/tr_a.log 2>&1; timeout 2400 python3 -I transcribe.py $S/work78/audio_b.wav $S/work78/tr_b.json > $S/work78/tr_b.log 2>&1; touch $S/work78/tr.done) &
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,fps=30"
ffmpeg -nostdin -v error -y -i ../dl77/input.bin -map 0:v:0 -map 0:a:0 -vf "$TM" -c:v libx264 -crf 12 -preset fast -c:a aac -b:a 192k -ar 48000 -ac 2 master_a.mp4
ffmpeg -nostdin -v error -y -i ../dl78/input.bin -map 0:v:0 -map 0:a:0 -vf "$TM" -c:v libx264 -crf 12 -preset fast -c:a aac -b:a 192k -ar 48000 -ac 2 master_b.mp4
printf "file 'master_a.mp4'\nfile 'master_b.mp4'\n" > cat.txt
ffmpeg -nostdin -v error -y -f concat -safe 0 -i cat.txt -c copy master1080.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 master_a.mp4 > dur_a.txt
ffmpeg -nostdin -v error -y -i master1080.mp4 -vf scale=720:1280 -c:v libx264 -crf 18 -preset fast -c:a aac -b:a 160k proxy.mp4
ffmpeg -nostdin -v error -y -i master1080.mp4 -map 0:a:0 -ac 1 -ar 16000 audio.wav
touch mp.done
wait
