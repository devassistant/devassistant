#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

//This section is used for writing some characters to file
int writeFile()
{
	FILE * f;
	char * tmpBuf = "This is simple example how to write simple string to file";
	f = fopen("/tmp/fileTest","wt");
	if ( f == NULL)
		return 1;
	fprintf(f,"%s\n",tmpBuf);
	fflush(f);
	fclose(f);
	return 0;
}

//This section is used for reading some characters from file
int readFile()
{
	FILE * f;
	char * tmpBuf;
	long lSize;
	f = fopen("/tmp/fileTest","rt");
	if ( f == NULL)
		return 1;
	fseek (f, 0, SEEK_END);
	lSize = ftell(f);
	printf("Length of file is: %d\n",lSize);
	fseek (f, 0, SEEK_SET);
	tmpBuf = (char *)malloc(sizeof(char)*lSize);
	size_t n = fread(tmpBuf,1,lSize,f);
	if (n == lSize)
	{
		printf("Ouput from file is: %s\n",tmpBuf);
	}
	else
	{
		printf("Reading failed %d\n",n);
		return 1;
	}
	free(tmpBuf);
	fclose(f);
	return 0;
}

int main (int argc,char * argv[])
{
	printf("Hello World\n");

	if(writeFile()==0)
		printf("Writing to file was successfull\n");
	else
	{
		printf("Writing to file failed\n");
		exit(1);
	}
	if(readFile()==0)
		printf("Reading from file was successfull\n");
	else
	{
		printf("Reading from file failed\n");
		exit(1);
	}

	return 0;
}
