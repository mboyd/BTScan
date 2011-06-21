all: btscan

btscan: btscan.c
	gcc -Wall -O -o btscan btscan.c -lbluetooth
clean:
	rm -f btscan
