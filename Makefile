UV ?= uv

.PHONY: all setup run test
all:
	$(UV) sync --locked

setup:
	sudo modprobe uinput
	printf '%s\n' 'SUBSYSTEM=="misc", KERNEL=="uinput", TAG+="uaccess"' | sudo tee /etc/udev/rules.d/70-mesa-usb.rules >/dev/null
	sudo udevadm control --reload-rules
	sudo udevadm trigger --settle --action=add --subsystem-match=misc --sysname-match=uinput
	@test -w /dev/uinput || { echo 'Sem acesso a /dev/uinput. Saia da sessão gráfica local, entre de novo e rode make run.' >&2; exit 1; }

run:
	$(UV) run --locked -m src

test:
	$(UV) run --locked -m unittest discover -s tests -v
