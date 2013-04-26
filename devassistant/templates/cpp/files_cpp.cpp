#include <iostream>
#include <fstream>
#include <string>
#include <cstdlib>

using namespace std;

int writeFile()
{
    ofstream testFile ("/tmp/cppTestFile");
    cout << "Now we will write some text to fire /tmp/cppTestFile" << endl;
    if(testFile.is_open())
    {
        testFile << "This is basic line,\n";
        testFile << "Created by C++ Development Assistant\n";
        testFile.close();
        cout << "Text has been written to file successfully" << endl;
    }
    else
    {
        cout << "Unable to open file";
        return 1;
    }
    return 0;
}

int readFile()
{
    string line;
    ifstream testFile ("/tmp/cppTestFile");
    cout << "Read text from file /tmp/cppTestFile" << endl;
    if(testFile.is_open())
    {
        while (testFile.good())
        {
            getline(testFile,line);
            cout << line << endl;
        }
        testFile.close();
        cout << "Reading operation was successfull" << endl;
    }
    else
    {
        cout << "Unable to open file" << endl;
        return 1;
    }
    return 0;
}

int main(){

        if (writeFile()!=0)
        {
            cout << "Could create and write to file" << endl;
            exit(1);
        }

        if(readFile()!=0)
        {
            cout << "Could not read from file" << endl;
            exit(1);
        }
}
       
