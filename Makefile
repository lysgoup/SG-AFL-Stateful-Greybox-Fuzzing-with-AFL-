stt:
	gcc -o stt stt.c -L cJSON/ -l cjson

stt2:
	gcc -o stt2 stt_timer.c -L cJSON/ -l cjson

stt_ori:
	gcc -o stt_ori stt_timer.c -L cJSON/ -l cjson

stt_probe:
	gcc -o stt_probe stt_timer.c -L cJSON/ -l cjson

clean:
	rm -rf stt
