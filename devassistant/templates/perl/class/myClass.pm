package myClass;

use strict;
use warnings;

sub new {
    my $class = shift;
    my $self = {
        _hotelName => shift,
        _street => shift,
        _name => shift,
        _date => undef
    };
    bless $self, $class;
    return $self;
}

sub enterBookedDate {
    my ($self) = shift;
    my $date = shift;
    $self->{_date} = $date;
}

sub getHotelName {
    my $self = shift;
    return $self->{_hotelName};
}

sub getStreet {
    my $self = shift;
    return $self->{_street};
}

sub getGuestName {
    my $self = shift;
    return $self->{_name};
}

sub getBookedDate {
    my $self = shift;
    return $self->{_date};
}

1;
