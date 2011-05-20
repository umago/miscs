/* Task Affinity - Make threads run on specific cores.
   Copyright (C) 2010 Lucas Alvares Gomes <lucasagomes@gmail.com>.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>. */

#include <stdio.h>
#include <dirent.h> 
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sched.h>
#include <linux/kernel.h>

void print_tasks(pid_t pid){
    DIR *d;
    struct dirent *dir;
    char path[25];
    sprintf(path, "/proc/%d/task/", (int) pid);
    d = opendir(path);
    if (d) {
        printf("TASKS: \n");
        while((dir = readdir(d)) != NULL) {
            if(strcmp( dir->d_name, ".") == 0 || 
               strcmp( dir->d_name, "..") == 0 ) {
              continue;
            }
          printf("\t%s\n", dir->d_name);
        }
        closedir(d);
    }
}

int main(int argc, const char *argv[])
{
    int cores= 0;
    pid_t pid; 
    cpu_set_t set;
    unsigned core = 0;
    struct task_struct *t;
    char input[50];
    
    if (argc <= 1){
        printf("%s <PID>\n", argv[0]);
        exit(1);
    }
    
    pid = atoi(argv[1]);

    cores = sysconf(_SC_NPROCESSORS_ONLN);
    printf("\nYour machine has %d cpus.\n\n", cores);

    print_tasks(pid);

    while(1) {
        printf("\n[Set] TASK CORE: ");
	fgets(input, sizeof(input), stdin);
	sscanf(input, "%u %u", &pid, &core);
 
        CPU_ZERO(&set);
        CPU_SET(core, &set);

        if (sched_setaffinity(pid, sizeof(cpu_set_t), &set))
            fprintf(stderr, "Error setting affinity for task %d\n", pid);

    }

    return 0;
}
