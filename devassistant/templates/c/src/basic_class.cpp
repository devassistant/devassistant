#include "basic_class.h"

BankAccount::BankAccount(string bankName, string bankCurrency, long bankDeposit)
{
    name = bankName;
    currency = bankCurrency;
    deposit = bankDeposit;
};

BankAccount::~BankAccount(){
//This can be used for closing threads
//or for closing server connection
}

int main()
{
    BankAccount bank1("Bank1", "EURO", 12000000);
    BankAccount bank2("Bank2", "USD", 15000000);

    cout << "Account name is:" << bank1.GetName() << endl;
    cout << "Deposit of bank " << bank1.GetName() << " is:" << bank1.GetDeposit() <<" " << bank1.GetCurrency() << endl;
    cout << "Account name is:" << bank2.GetName() << endl;
    cout << "Deposit of bank " << bank2.GetName() << " is:" << bank2.GetDeposit() <<" " << bank2.GetCurrency() << endl;
}
