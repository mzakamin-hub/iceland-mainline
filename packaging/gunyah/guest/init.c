// SPDX-License-Identifier: GPL-2.0-only
/*
 * /init of the Gunyah test guest: one GUEST-HELLO line, then PSCI SYSTEM_OFF. Built with the kernel's nolibc.
 *
 * The line goes out twice: through /dev/kmsg (printk; the console code prints every record before the kernel's own
 * "reboot: Power down" line) and through the tty on /dev/console. The guest UART has no interrupt, so the 8250
 * driver drains its tty buffer from a poll timer: wait for the tty to drain (TCSBRK 1 = tcdrain) and give it 200 ms
 * more before the power-off, else the line is cut (seen on the first run: "GUEST-HELLO: Lin").
 */
#include <asm/ioctls.h>
#include <linux/reboot.h>

static void kmsg(const char *s, int n)
{
	int fd = open("/dev/kmsg", O_WRONLY);

	if (fd >= 0) {
		write(fd, s, n);
		close(fd);
	}
}

int main(void)
{
	struct utsname u;
	char line[256];
	int n;

	if (uname(&u) == 0)
		n = snprintf(line, sizeof(line), "GUEST-HELLO: Linux %s %s running as a protected Gunyah VM\n",
			     u.release, u.machine);
	else
		n = snprintf(line, sizeof(line), "GUEST-HELLO: uname failed\n");
	if (n < 0)
		return 1;
	if (n >= (int)sizeof(line))
		n = sizeof(line) - 1;
	kmsg(line, n);
	write(1, line, n);
	ioctl(1, TCSBRK, 1);
	msleep(200);
	reboot(LINUX_REBOOT_CMD_POWER_OFF);
	printf("GUEST-HELLO: reboot returned\n");
	return 1;
}
