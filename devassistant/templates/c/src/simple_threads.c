#include <pthread.h>

void print_message_function( void * ptr);
void do_one_thing(int *);
void do_another_thing(int *);
void do_wrap_up(int , int );

int r1 = 0, r2 = 0;

typedef struct str_thdata
{
	int thread_no;
	char message[100];
} thdata;

main()
{
	pthread_t thread1, thread2;
	pthread_t thread3, thread4;

	thdata data1, data2;
	data1.thread_no = 1;
	strcpy(data1.message, "Hello!");
	data2.thread_no = 2;
	strcpy(data2.message, "Hi!!");

	pthread_create(&thread1, NULL, (void *) do_one_thing, (void *) &r1);
	pthread_create(&thread2, NULL, (void *) do_another_thing, (void *) &r2);

	pthread_join(thread1, NULL);
	pthread_join(thread2, NULL);

	pthread_create(&thread3, NULL, (void *) &print_message_function, (void *) &data1);
	pthread_create(&thread4, NULL, (void *) &print_message_function, (void *) &data2);

	pthread_join(thread3, NULL);
	pthread_join(thread4, NULL);

	do_wrap_up(r1,r2);

}

void do_one_thing(int *pnum_times)
{
	int i,j,x;
	for(i = 0; i<4; i++)
	{
		printf("doing one thing\n");
		for(j=0;j<10000;j++) x = x+i;
		(*pnum_times)++;
	}
}


void do_another_thing(int *pnum_times)
{
	int i,j,x;
	for(i = 0; i<4; i++)
	{
		printf("doing another thing\n");
		for(j=0;j<10000;j++) x = x+i;
		(*pnum_times)++;
	}
}

void do_wrap_up(int one_times, int another_times)
{
	int total;
	total = one_times + another_times;
	printf("All done, one thing %d, another %d for a total of %d\n", one_times, another_times, total);
}

void print_message_function(void *ptr)
{
	thdata * data;
	data = (thdata *) ptr;
	printf("Thread %d says %s \n", data->thread_no,data->message);

	pthread_exit(0);
}
