#!/usr/bin/env perl

while (<>) {
    if (m{<seg[^>]*>(.*)</seg>}) {
        $seg = $1;
	$seg =~ s/&lt;/</g;
	$seg =~ s/&gt;/>/g;
	$seg =~ s/&amp;/&/g;
	$seg =~ s/\s+ / /g; $seg =~ s/^ //; $seg =~ s/ $//;
        print "$seg\n";
    }
}
