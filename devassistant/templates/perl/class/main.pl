#!/usr/bin/perl

#use strict;
use warnings;

use POSIX qw(strftime);

use myClass;

my $myClass = new myClass( "Holiday", "Baker Street", "Sherlock Holmes");
my $tm = strftime "%m/%d/%Y", localtime;
$myClass->enterBookedDate($tm);

print ("The hotel name is ". $myClass->getHotelName() . "\n");
print ("The hotel street is ". $myClass->getStreet() . "\n");
print ("The hotel is booked on the name ". $myClass->getGuestName() . "\n");
print ("Accomodation starts at " . $myClass->getBookedDate() . "\n");

