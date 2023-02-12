#!/usr/bin/perl
#use strict;

eval {
      use lib '.';
      require "vars.cgi";  #load up common variables and routines. // &cgierr
      };
warn $@ if $@;

if ($@)
   {
    print "Content-type: text/plain\n\n";
    print "Error including libraries: $@\n";
    print "Make sure they exist, permissions are set properly, and paths are set correctly.";
    exit;
    }

#globals
my %in;
my %Words_Length_Letter_Posn = (); #multiple hashes of words indexed by [length][position][ord(letter)]
# $Words_Length_Letter_Posn[length][position][ord(letter)]{$word} = 1
#a useless value of 1 is used to initialize the hash
#we only use this hash to keep a list of keys which is a list of words of [length][position][ord(letter)]
#a hash (vice a list) is used so we don't have duplicate words!!!!!
my @WordsOfLength = (); #@{$WordsOfLength[$length]} # hash , $WordsOfLength[$length]} returns a list of words of $length
my @puzzle=(); #the puzzle with the words inserted. array[][] of hash  $puzzle[][]->{Letter}   @{$puzzle[][]->{WordsAtPos}}
#$puzzle[0][0]='';
#my @NextSquare=(); #will return an x,y array showing the next square in the word  $NextSquare[$x][$y][$dir]
my %words_that_are_inserted = (); #hash of hashes.
my $PadChar = chr(178);
my $unoccupied = ' ';
my $MinWordLength = 3;
my $MaxWordLength = 51;
my $Ignore_Crosses = 1; #if 1 then we we can have solitary words on the grid without crossing
#$dir = 0 is a horiz word 1 is a vertical word
my %clues;
my $hints_across;
my $hints_down;
#my @WordsAtPosition = (); #array[][] of list  access by @{$WordsAtPosition[$x][$y]}
my $debug = 0;

eval { &main; };                            # Trap any fatal errors so the program hopefully
if ($@) { &cgierr("fatal error: $@"); }     # never produces that nasty 500 server error page.
exit;   # There are only two exit calls in the script, here and in in &cgierr.

sub main
{
my @temp;
my $x;
my $y;

if ($debug == 1) {open (LOGG, ">log.txt") or die("log.txt failed");};

print "Content-type: text/html\n\n";

%in = &parse_form; #get input arguments

&process_arguments();
&initialize_grid();
if ($debug == 1) {print LOGG "Entering \&load_word_list()\n\n"}
&load_word_list();
$time_to_quit = time() + $in{timeout};
if ($debug == 1) {print LOGG "Entering \&build_puzzle()\n\n"}
&build_puzzle(); #in $puzzle[][] of course
&number_clue_list();

my $solved_puzzle = "";
$solved_puzzle = &print_solved_puzzle();
my $puzzle_string = &print_puzzle();

open (DATA, "<./templates/index.html") or die("Template file /templates/index.html does not exist");
my @DATA = <DATA>;
close (DATA);
my $template_file = join('' , @DATA);

$template_file =~ s/<%answers%>/$solved_puzzle/g;
$template_file =~ s/<%across%>/$hints_across/g;
$template_file =~ s/<%down%>/$hints_down/g;
$template_file =~ s/<%down%>/$hints_down/g;
$template_file =~ s/<%puzzle%>/$puzzle_string/g;
$template_file =~ s/\%archivepath\%/$archivepath/g;
$template_file =~ s/\%archiveurl\%/$archiveurl/g;

#archive the puzzle!
#open (DATA, "<count") or sysopen(DATA, 'count', O_CREAT|O_RDWR , 0666);
#$count = <DATA>;
#close (DATA);
#$count++;
#open (DATA, ">count") or die("count file cannot be written too");
#print DATA $count;
#close (DATA);
#$filename = sprintf("%05d", $count);

$title = time();
$template_file =~ s/\%title\%/$title/g;
$filename .= "$title\.html";

$template_file =~ s/\%filename\%/$filename/g;
print $template_file;

#write archice file
if (not -d ($archivepath)) {mkdir("$archivepath")  or die("Could not create archive path $archivepath");}
open (DATA, ">$archivepath/$filename") or die("Could not create archive file $filename");
print DATA $template_file;
close (DATA);

print qq|<META HTTP-EQUIV="Refresh" CONTENT="0; URL=$archivepath/$filename">|; #name is for chat

if ($debug == 1) {close (LOGG)}
}

sub number_clue_list()
{
my $x = -1;
my $y = -1;
my @word_sort;
my ($temp , $temp2);
my @temp;
my $word;

foreach $word (keys %words_that_are_inserted) #create an array of 1. the word 2. the start x pos 3. the start y pos
         {
         push @temp , [$word , $words_that_are_inserted{$word}{startx}  ,$words_that_are_inserted{$word}{starty}];
         }

#sort the words so we can number across, down, across
@temp = sort {$a->[1] <=> $b->[1]} @temp; #sort word list on x stat position
@temp = sort {$a->[2] <=> $b->[2]} @temp; #sort word list on y start position

#set word numbers. words that start in same square have same number!
my $number = 0;
$hints_across = "";
$hints_down = "";
foreach my $temp (@temp)
         {
         $word = $temp->[0];
         if (($temp->[1] != $x) or ($temp->[2] != $y)) #keep same number for same square. if last word did not start in same square increase the clue number
               {$number++}
         $words_that_are_inserted{$word}->{number} = $number;
         $x = $temp->[1];
         $y = $temp->[2];

         #build an array of all letter positions for word so javascript can cycle through typing spots
         $xx = $x;
         $yy = $y;
         $dir = $words_that_are_inserted{$word}{dir};
         $LetterPosArray = '';
         for ($temp2 = 0; $temp2 < length($word); $temp2++)
            {
            $LetterPosArray .= "$xx,$yy,";
            $xx = $xx + not ($dir);
            $yy  = $yy + $dir;
            }
         #print "$wordposarray";
         chop $LetterPosArray; #remove trailing comma
         $words_that_are_inserted{$word}->{LetterPosArray} = $LetterPosArray;

         if ($words_that_are_inserted{$word}{dir} == 0)
              {
              $hints_across .= qq|
              $number\. <a href="\#self" id="$word" class="clues" ONCLICK="choose('$word' , $words_that_are_inserted{$word}->{startx} , $words_that_are_inserted{$word}->{starty} , [$words_that_are_inserted{$word}->{LetterPosArray}]);">$clues{$word}</a>
              &nbsp;&nbsp;&nbsp;&nbsp;
              <font size=-1><i><A ONCLICK="if (this.innerHTML=='show') {this.innerHTML='$word'} else {this.innerHTML='show'}" HREF="\#self">show</A></i></font></br>
              |;
              }
         if ($words_that_are_inserted{$word}{dir} == 1)
              {
              $hints_down .=
              qq|
              $number\. <a href="\#self" id="$word" class="clues" ONCLICK="choose('$word' , $words_that_are_inserted{$word}->{startx} , $words_that_are_inserted{$word}->{starty} , [$words_that_are_inserted{$word}->{LetterPosArray}]);">$clues{$word}</a>
              &nbsp;&nbsp;&nbsp;&nbsp;
              <font size=-1><i><A ONCLICK="if (this.innerHTML=='show') {this.innerHTML='$word'} else {this.innerHTML='show'}" HREF="\#self">show</A></i></font></br>
              |;
              }
         }
};

sub build_puzzle()
{
my @temp;
my $x;
my $y;
my $x_start;
my $y_start;

$Ignore_Crosses = 1; #ignore word crosses as we are now just filling the top and left rows
#add words all across top row
$x = 0;
$y = 0;
while ($x + $MinWordLength < $in{width})
        {
        @temp = &Insert(&Random_Word_From(&WordsThatFitAt($x , $y , 0)));
        $x = $x + length($temp[3]) + 1; #add one for the blank at end of word.
        }

$x = 0;
# add words all across left column
while ($y + $MinWordLength < $in{height})
        {
        @temp = &Insert(&Random_Word_From(&WordsThatFitAt($x , $y , 1)));
        $y = $y + length($temp[3]) + 1; #add one for the blank at end of word.
        }


# go through every ocuppied square and check for possible word placements. start across then try down
$Ignore_Crosses = 0; #now insist that words cross as the top and left framework are set
#$Ignore_Crosses = 1;
while (time() < $time_to_quit)
         {
         $x = 0;
         $y = 0;
         $x_start = 0;
         $y_start = 0;

        while (($x_start < $in{width}) and ($y_start < $in{height}))
                 {
                 #across
                 $y = $y_start;
                 for ($x = $x_start; $x < $in{width}; $x++)
                       {
                       if  (time() > $time_to_quit ) {last}
                       #check every square in sequence and try both horiz and vertical words. KISS!
                       if ($debug == 1) {print LOGG "Try inserting word across at $x,$y\n\n"}
                       &Insert(&Random_Word_From(&WordsThatFitAt($x , $y , 0)));
                       if ($debug == 1) {print LOGG "Try inserting word down at $x,$y\n\n"}
                       &Insert(&Random_Word_From(&WordsThatFitAt($x , $y , 1)));
                       }
                 #down
                 $x = $x_start;
                 for ($y = $y_start; $y < $in{height}; $y++)
                       {
                       if  (time() > $time_to_quit ) {last}
                       #check every square in sequence and try both horiz and vertical words. KISS!
                       if ($debug == 1) {print LOGG "Try inserting word Down at $x,$y\n\n"}
                       &Insert(&Random_Word_From(&WordsThatFitAt($x , $y , 0)));
                       if ($debug == 1) {print LOGG "Try inserting word across at $x,$y\n\n"}
                       &Insert(&Random_Word_From(&WordsThatFitAt($x , $y , 1)));
                       }
                 if  (time() > $time_to_quit ) {last}
                 $x_start++;
                 $y_start++;
                 }
         }

if ($debug == 1) {print LOGG "Finished inserting words.\n\n"}

#fill unoccupied squares with pad character
$x = 0;
$y = 0;
for ($y = 0; $y < $in{height}; $y++)
       {
        for ($x = 0; $x < $in{width}; $x++)
              {
              if ($puzzle[$x][$y]->{Letter} eq $unoccupied)
                   {$puzzle[$x][$y]->{Letter} = $PadChar}
              }
        }

};

sub process_arguments()
{
#process input arguments
# Test inputs to see if they are valid and set defaults

#defaults
if ( (not $in{width}) or ($in{width} !~ /^\d+$/ ) ) {$in{width} = 19;}
if ( (not $in{timeout}) or ($in{timeout} !~ /^\d+$/ ) ) { $in{timeout} = 5; }

#set bounds
if  ($in{timeout} > 30)  { $in{timeout} = 30; }
if ($in{width} > 51) {$in{width} = 51;}
if ($in{width} < 9) { $in{width} = 9;}

if ( ($in{min} < 1) or ($in{min} !~ /^\d+$/) ) { $in{min} = 3;}
if ( ($in{max} >51) or ($in{max} !~ /^\d+$/) ) { $in{max} = 51;}
$MinWordLength = $in{min};
$MaxWordLength = $in{max};

if ($MaxWordLength > $in{width}) {$MaxWordLength = $in{width}} #no sense in loading words that won't fit on the grid

$in{height} = $in{width};
};

sub load_word_list()
{
my @word_list;
my @DATA;
my $line;
my $word;
my $clue;
my $length;
my $LetterPosition;
my $letter;
my @cluefiles = split('~~' , $in{cluefiles}); #all our checkbox values with same name are separated by ~~
my $temp;

if (not $in{cluefiles}){@cluefiles = "words/CrosswordExpress.txt"}

foreach $temp (@cluefiles)
         {
         open (DATA, "<$temp") or die("Word file $temp does not exist");
         #@DATA = <DATA>;
         push @DATA , <DATA>;
         close (DATA);
         }

foreach $line (@DATA)
         {
         $line =~ s/\n//g; #remove line return
         ($word , $clue) = split(/\|/,$line);

         $word = uc($word); #all words must be uppercase for standard, display and search reasons.

         #does word already exist?
         if (exists $clues{$word})
             {
             if (rand() < 0.5) {$clues{$word} = $clue;} #We already have a clue for this word. 50% chance we will use new clue. gives gausian curve, but adaquate for 5 or less clues.
             next; #go get next line as we have already processed this $word
             };

         $length = length($word);
         if ($length < $MinWordLength) {next}; #ignore little letter words
         if ($length > $MaxWordLength) {next}; #ignore big letter words

         #build just a word list
         push @word_list , $word;

         #create a hash for word => clue
         $clues{$word} = $clue;

         push @{$WordsOfLength[$length]} , $word; #build a array of lists. a list for each possible word length

         $LetterPosition = 0;
         #create a hash of words for each letter in each letter
         foreach $letter (split('' , $word))
                  {
                   #add word to a hash (and therefore a list using keys) accessed by an array indexed by [word length][ord(Letter)][LettePosition] with true value for quick lookup!
                  $Words_Length_Letter_Posn[$length][ord($letter)][$LetterPosition]{$word} = 1;
                  $LetterPosition++;
                  };
         };
};

sub WordsWithLengthAndLetterInNthPosn()
{
#input
# $_[0] length of word
# $_[1] take a letter
# $_[2] and word position 0 - ?
#return list of words that match
return keys %{$Words_Length_Letter_Posn[$_[0]][ord($_[1])][$_[2]]};
}

sub initialize_grid()
{
my $x;
my $y;

# Initialize puzzle grid
for ($y = 0; $y < $in{height}; $y++)
      {
      for ($x = 0; $x < $in{width}; $x++)
            {
            if ( ($y % 2 != 0) and ($x % 2 != 0) )
                   {
                   $puzzle[$x][$y]->{Letter} = $PadChar; #PadChar indicate a letter will never go in this spot.
                   }
            else
                {
                $puzzle[$x][$y]->{Letter} = $unoccupied;
                }
            }
      }
};

sub print_puzzle()
{
my ($a,$temp,$temp2,$temp3,$temp4);
my $y;
my $x;
my $word;

# Initialize puzzle grid with just white and black (no letters or numbers)
for ($y = 0; $y < $in{height}; $y++)
      {
      for ($x = 0; $x < $in{width}; $x++)
            {
            if ( $puzzle[$x][$y]->{Letter} =~ /\w/ )
                   {
                   $puzzle[$x][$y]->{Letter} = $unoccupied;
                   }
            else
                {
                $puzzle[$x][$y]->{Letter} = $PadChar; #PadChar indicate a letter will never go in this spot.
                }
            }
      }

foreach $word (keys %words_that_are_inserted)
         {
         $puzzle[$words_that_are_inserted{$word}->{startx}][$words_that_are_inserted{$word}->{starty}]->{Letter} = $words_that_are_inserted{$word}->{number}
         }

$temp = "<table cellspacing='0' cellpadding='0' CLASS='tableclass'>";
for ($y = 0; $y < $in{height}; $y++)
        {
        $temp .= "<tr>";
                for ($x = 0; $x < $in{width}; $x++)
                      {
                      $temp2 = @{$puzzle[$x][$y]->{WordsAtPos}}[0];
                      $temp3 = "";
                      foreach $a (@{$puzzle[$x][$y]->{WordsAtPos}}) #for each word (up to two) at each square, do the following
                            {
                            if ($words_that_are_inserted{$a}{dir} == 0)
                                 {
                                 $dir = "Across";
                                 }
                            else
                                {
                                $dir = "Down";
                                }
                            $temp3 .= "$words_that_are_inserted{$a}{number} $dir: $clues{$a} \n";  #create clue hover text for each square!
                            }

                      $temp4 = ""; #clear the soon to be choose() routine variable
                      if ( scalar(@{$puzzle[$x][$y]->{WordsAtPos}}) == 2 ) # if there are two words crossing at this square
                           {#build a choice for horiz or vertical selections
                           foreach $a (@{$puzzle[$x][$y]->{WordsAtPos}})
                                    {
                                    if ($words_that_are_inserted{$a}{dir} == 0)
                                         {
                                         $temp4 .= qq|if (horizvert == $words_that_are_inserted{$a}{dir}) {choose("$a" , $x , $y , [$words_that_are_inserted{$a}->{LetterPosArray}])};|;
                                         }
                                    else
                                        {
                                        $temp4 .= qq|if (horizvert == $words_that_are_inserted{$a}{dir}) {choose("$a" , $x , $y , [$words_that_are_inserted{$a}->{LetterPosArray}])};|;
                                        }
                                    }
                           }
                      else
                          {#just choose the one word
                          $temp4 = qq|choose("$temp2" , $x , $y , [$words_that_are_inserted{$temp2}->{LetterPosArray}]);|;
                          }
                      $temp4 .= 'ToggleHV();';

                      if ($puzzle[$x][$y]->{Letter} eq $PadChar) #make sure our page width is fixed
                             {$temp .= "<td CLASS='tdblackclass'><spacer width='20 pt'></td>";}
                      if ($puzzle[$x][$y]->{Letter} =~ /[0-9]/)
                            {
                            $temp .= qq|
                            <TD VALIGN='TOP' ALIGN='LEFT' CLASS='tdnumberclass'>
                            <DIV  style='position: absolute; z-index: 2;'>$puzzle[$x][$y]->{Letter}</DIV>
                            <TABLE CELLPADDING="0" CELLSPACING="0">
                                  <TBODY>
                                         <TR>
                                                <TD title='$temp3' CLASS='tdwhiteclass' ID='cell_$x\_$y'
                                                ONCLICK='$temp4' VALIGN='middle' WIDTH='20' ALIGN='center'
                                                HEIGHT='25'>&nbsp;</TD>
                                         </TR>
                                  </TBODY>
                                </TABLE>
                            </TD>
                            |;
                            }
                      if ($puzzle[$x][$y]->{Letter} =~ /$unoccupied/)
                            {
                            $temp .= qq| <td title='$temp3' ID='cell_$x\_$y' CLASS='tdwhiteclass' ONCLICK='$temp4';>&nbsp;</td>|;
                            }
                      }
        $temp .= "</tr>\n";
        }

$temp .= "</table>\n";
return $temp;
};

sub print_solved_puzzle()
{
my $temp;
my $y;
my $x;

$temp = "<table cellspacing='0' CLASS='tableclass'>";
for ($y = 0; $y < $in{height}; $y++)
        {
        $temp .= "<tr>";
                for ($x = 0; $x < $in{width}; $x++)
                      {
                      if ($puzzle[$x][$y]->{Letter} eq $PadChar)
                             {$temp .= "<td CLASS='tdblackclass'></td>";next;}
                      if ($puzzle[$x][$y]->{Letter} =~ /[a-zA-Z$unoccupied]/)
                            {$temp .= "<td CLASS='tdwhiteclass'>$puzzle[$x][$y]->{Letter}</td>"}
                      }
        $temp .= "</tr>\n";
        }
$temp .= "</table>\n";
return $temp;
};

sub Random_Word_From()
{
# Random_Word_From(x,y,dir,listofwords)
my $x = shift @_;
my $y = shift @_;
my $dir = shift @_;
my $randomword;
my $temp;

if ($debug == 1) {print LOGG "Start of \&Random_Word_From()\n\n"}

if (scalar(@_) == 0) #if there are no words to choose from, we will return a blank word.
    {return ($x , $y , $dir , '')}

do
    {
    $temp = rand(@_); #random index of our list of words
    $randomword = $_[$temp]; #get the word
    delete $_[$temp]; #remove it from the list of words
    #if ($debug == 1) {print LOGG "Looping in Random_Word_From() $randomword\n\n"}
    }
#until (not ($words_that_are_inserted{$randomword}) or (@_ == ()));
until ((not defined($words_that_are_inserted{$randomword})) or (@_ == ()));
#quit only if we empty the potential word list OR  we find a word in the potential word list that has not been been used before

if ($debug == 1) {print LOGG "Leaving \&Random_Word_From()\n\n"}

return ($x , $y , $dir , $randomword);
};

sub RandomPosAndDirection()
{
my $x=1;
my $y=1;
my $dir;

#while (on a pad OR letter before chosen spot)
while ( ($x%2==1 and $y%2==1) or ($puzzle[$x - (not $dir)][$y - $dir]->{Letter} =~ /\w/) )
        {
        $x = int(rand($in{width}));
        $y = int(rand($in{height}));
        $dir = int(rand(2));
        if ($x%2==1) {$dir = 0;}
        if ($y%2==1) {$dir = 1;}
        }
return ($x , $y , $dir);
};

sub IsLetterBeforeStart
{
#IsLetterBeforeStart($x , $y , $dir)
my $x = $_[0];
my $y = $_[1];
my $dir = $_[2];

if (($x == 0) and ($dir == 0)) {return(0)} #we are at the edge so ignore rest
if (($y == 0) and ($dir == 1)) {return(0)} #we are at the edge so ignore rest
if (($puzzle[$x - not($dir)][$y - $dir]->{Letter} =~ /\w/)) {return(1)} #this word would but up against an existing word. FaiL!
return(0);
};

sub WordsThatFitAt()
{
#WordsThatFitAt(x,y,dir)
my $x = $_[0];
my $y = $_[1];
my $dir = $_[2];
my $temp = '';
my $temp2 = '';
my @mask = (); #will be all existing characters and spaces at $x $y in $dir
my @word_list = ();

if ($debug == 1) {print LOGG "Start of \&WordsThatFitAt()\n\n"}

if (&IsLetterBeforeStart($x , $y , $dir))
     {
     if ($debug == 1) {print LOGG "Thete was \&IsLetterBeforeStart() So exiting \&WordsThatFitAt()\n\n"}
     return($x , $y , $dir , ())
     } #a word in this spot x,y dir, would butt up against an existing word. So fail!

$temp = $puzzle[$x][$y]->{Letter}; #get next possible grid letter
$temp2 = $puzzle[$x + (not $dir)][$y + $dir]->{Letter}; #get next next possible grid letter

until ( ($x >= $in{width} or $y >= $in{height}) or ($temp eq $PadChar) or (($temp =~ /\w/) and ($temp2 =~ /\w/)))
#word cannot go any farther if 1. out of bounds 2. we hit a pad character 3. hit word going in same direction, identified by two letters in a row detected
 {
 if ($debug == 1) {print LOGG "Loop in \&WordsThatFitAt()\n\n"}
 push @mask,$temp; #add letter or space to mask
 #if (not (($temp =~ $unoccupied) and ($temp2 =~ /\w/))) #ignore cases where the last letter is a space before a letter. The possible word would butt against another word, not join or cross it
 if (not ($temp2 =~ /\w/)) #ignore cases where the last letter of a word would but up against an existing letter. The possible word would butt against another word, not join or cross it
 #if ($temp2 =~ /\W/) #ignore cases where the last letter of a word would but up against an existing letter. The possible word would butt against another word, not join or cross it
        {push @word_list , &ListFromMask(@mask)} #add possible words for partial mask

 $x = $x + (not $dir); $y = $y + $dir;
 $temp = $puzzle[$x][$y]->{Letter}; #get next possible grid letter
 $temp2 = $puzzle[$x + (not $dir)][$y + $dir]->{Letter}; #get next next possible grid letter
 }

if ($debug == 1) {print LOGG "Exiting \&WordsThatFitAt()\n\n"}
return($_[0] , $_[1] , $dir , @word_list);
};

sub ListFromMask()
{
my @mask = @_; #eg: A_PL_
my $temp;
my $temp2 = 0;
my $temp3 = 0; #tells us if we have ANY letters in the mask AND whether we have found a mask letter yet!
my $temp4;
my @word_list = ();
my $length = scalar @mask;
my @intersection_word_list;

if ($debug == 1) {print LOGG "Entering \&ListFromMask()\n\n"}
if ($debug == 1) {print LOGG "Mask:" , @mask , "\n\n"}

foreach $temp (@mask)
         {
         if ($temp =~ /\w/) #get a list(s) of words for each letter found in the mask. Then we intersect all the lists.
              {
              @word_list = &WordsWithLengthAndLetterInNthPosn($length,$temp,$temp2);
              if ($temp3 == 1) #only intersect after we have a list to intersect with , IE: after the first mask letter
                   {
                   @intersection_word_list = &intersection(\@intersection_word_list , \@word_list);
                   }
              else
                  {
                  @intersection_word_list = @word_list;
                  }
              $temp3 = 1; #lettrs are in the mask
              }
         $temp2 = $temp2 + 1;
         }
@word_list = ();

if ($temp3 == 0) #there were no letters in @mask, use @all_word_list
     {
     @intersection_word_list = @{$WordsOfLength[$length]};
     }
if ($debug == 1) {print LOGG "Exiting \&ListFromMask()\n\n"}
return @intersection_word_list;
};

sub Insert()
{
my $x = $_[0];
my $y = $_[1];
my $dir = $_[2];
my $word = $_[3];
my $temp;
my $temp2;
my @temp;
my $temp3;

if ($debug == 1) {print LOGG "Entering \&Insert()\n\n"}

if ($word eq '')
     {
     if ($debug == 1) {print LOGG "No Words Fit at $x $y $dir\n\n"}
     return($x , $y , $dir , '')
     } #no word can fit at this location

@temp = split(// , $word); #split word into letters

$temp2 = 0;
#see how many times we have crossed another word
if ($Ignore_Crosses == 0)
     {
     foreach $temp (@temp)
         {
         if ($puzzle[$x][$y]->{Letter} =~ /\w/)
              {
              $temp2++;
              }

         $x = $x + (not $dir);
         $y = $y + $dir;
         }
     if ($temp2 < 1)
          {
          if ($debug == 1) {print LOGG "Word did not cross. Exiting \&Insert()\n\n"}
          return($_[0] , $_[1] , $dir , '')
          } #fail if we don't cross at all
     }

$x = $_[0];
$y = $_[1];

#pad at start of word to avoid word butting
if (scalar(@temp) > 0) {$puzzle[$x - (not $dir)][$y - $dir]->{Letter} = $PadChar};

$temp2 = 0;
foreach $temp (@temp) #for each letter in the word
         {
         $puzzle[$x][$y]->{Letter} = $temp; #add letter to grid
         push @{$puzzle[$x][$y]->{WordsAtPos}} , $word; #add the word to an array for EACH crossword position so we know what words belong to what square

         $x = $x + (not $dir);
         $y = $y + $dir;
         $temp2 = $temp2 + 1;
         }
#pad at end of word to avoid word butting
if ($temp2 != 0) {$puzzle[$x][$y]->{Letter} = $PadChar};

 $words_that_are_inserted{$word}->{startx} = $_[0];
 $words_that_are_inserted{$word}->{starty} = $_[1];
 $words_that_are_inserted{$word}->{dir} = $dir;

if ($debug == 1) {print LOGG "Exiting \&Insert()\n\n"}
return ($_[0] , $_[1] , $dir , $word); # let other routines know what we have done
};

sub intersection()
{
#two lists must be passed by reference \@sfdsfds , \@dgffdsfds
#my @union = ();
my @intersection = ();
#my @difference = ();
my %count = ();

if ($debug == 1) {print LOGG "Entering \&intersection()\n\n"}

foreach my $element (@{$_[0]} , @{$_[1]})
        {
        $count{$element}++;
        } #count singles or duplicates in the lists

@intersection = grep {($count{$_} > 1)} keys(%count); #only pass to the list duplicates not single values
=pod
foreach $element (keys %count) #only pass to the list duplicates not single values
         {
         #push @union, $element;
         #push @{ $count{$element} > 1 ? \@intersection : \@difference }, $element;
         if ($count{$element} > 1){push @intersection , $element}
         }
=cut
if ($debug == 1) {print LOGG "Exiting \&intersection()\n\n"}
return(@intersection);
};
