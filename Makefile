all: btscan btscan-mips

btscan: btscan.c
	gcc -Wall -O -o btscan btscan.c -lbluetooth

btscan-mips: btscan.c
	mipsel-unknown-linux-uclibc-gcc -Wall -Os -o btscan.mips btscan.c -lbluetooth -L/home/user/Openwrt/backfire/staging_dir/target-mipsel_uClibc-0.9.30.1/usr/lib/ -I/home/user/Openwrt/backfire/staging_dir/target-mipsel_uClibc-0.9.30.1/usr/include/

clean:
	rm -f btscan btscan.mips
