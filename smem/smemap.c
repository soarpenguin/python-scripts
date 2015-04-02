/*
 smem - a tool for meaningful memory reporting

 Copyright 2008-2009 Matt Mackall <mpm@selenic.com>

 This software may be used and distributed according to the terms of
 the GNU General Public License version 2 or later, incorporated
 herein by reference.
*/

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/stat.h>
#include <memory.h>
#include <errno.h>
#include <fcntl.h>
#include <dirent.h>

struct fileblock;
struct fileblock {
	char data[512];
	struct fileblock *next;
};

int writeheader(int destfd, const char *path, int mode, int uid, int gid,
		int size, int mtime, int type)
{
	char header[512];
	int i, sum;

	memset(header, 0, 512);

	sprintf(header, "%s", path);
	sprintf(header + 100, "%07o", mode & 0777);
	sprintf(header + 108, "%07o", uid);
	sprintf(header + 116, "%07o", gid);
	sprintf(header + 124, "%011o", size);
	sprintf(header + 136, "%07o", mtime);
	sprintf(header + 148, "        %1d", type);

	/* fix checksum */
	for (i = sum = 0; i < 512; i++)
               sum += header[i];
	sprintf(header + 148, "%06o", sum);

	return write(destfd, header, 512);
}

int archivefile(const char *path, int destfd)
{
	struct fileblock *start, *cur;
	struct fileblock **prev = &start;
	int fd, r, size = 0;
	struct stat s;

	/* buffer and stat the file */
	fd = open(path, O_RDONLY);
	fstat(fd, &s);

	do {
		cur = calloc(1, sizeof(struct fileblock));
		*prev = cur;
		prev = &cur->next;
		r = read(fd, cur->data, 512);
		if (r > 0)
			size += r;
	} while (r == 512);

	close(fd);

	/* write archive header */
	writeheader(destfd, path, s.st_mode, s.st_uid,
		    s.st_gid, size, s.st_mtime, 0);

	/* dump file contents */
	for (cur = start; size > 0; size -= 512) {
		write(destfd, cur->data, 512);
		start = cur;
		cur = cur->next;
		free(start);
	}
}

int archivejoin(const char *sub, const char *name, int destfd)
{
	char path[256];
	sprintf(path, "%s/%s", sub, name);
	return archivefile(path, destfd);
}

int main(int argc, char *argv[])
{
	DIR *d;
	struct dirent *de;
	struct stat s;

	chdir("/proc");
	archivefile("meminfo", 1);
	archivefile("version", 1);

	d = opendir(".");
	while ((de = readdir(d)))
		if (de->d_name[0] >= '0' && de->d_name[0] <= '9') {
			stat (de->d_name, &s);
			writeheader(1, de->d_name, 0555, s.st_uid,
				    s.st_gid, 0, s.st_mtime, 5);
			archivejoin(de->d_name, "smaps", 1);
			archivejoin(de->d_name, "cmdline", 1);
			archivejoin(de->d_name, "stat", 1);
		}

	return 0;
}

