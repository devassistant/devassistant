#include <iostream>
#include <string>
using namespace std;

class BankAccount {
    public:
        BankAccount(string,string,long);
        ~BankAccount();
        string GetName() const { return name; }
        string GetCurrency() const { return currency; }
        long GetDeposit() const { return deposit; }
        void SetName(string bankName) { name = bankName; }
        void SetCurrency(string bankCurrency) { currency = bankCurrency; }
        void SetDeposit(long bankDeposit) { deposit = bankDeposit; }
    private:
        string name;
        string currency;
        long deposit;

};
