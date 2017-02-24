% LaTeX format for theses at CSLU
% 
% Based on "Guidelines and Regulations for Completion of Master's and PhD Degrees,"
% Section 4, "Instructions for Preparing the Master's Thesis or Doctoral Dissertation"
% http://www.ohsu.edu/xd/education/schools/school-of-medicine/academic-programs/graduate-studies/students/upload/Guidelines-and-Regulations-revised-9-2010.pdf
% Last referenced 2014/06/10
% 
% This document class attempts to adhere to the above guidelines as closely as possible.
% However, no guarantees are made as to the accuracy and acceptability of the resulting output.
% Use at your own risk.
% 
% Some portions are blindly copied from the outdated, but still-in-use ogi-thesis.sty.
% These portions likely require revision, and are not guaranteed to be up-to-date.
% 
% Latest version available at:
% http://gitlab.cslu.ohsu.edu/sniderb/cslu-thesis

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{cslu-thesis}[2014/06/24 CSLU thesis document]


% Document class options
\newif\ifcopyright
\copyrightfalse
\DeclareOption{copyright}{
    \copyrighttrue
}

\newif\iflistoftables
\listoftablesfalse
\DeclareOption{listoftables}{
    \listoftablestrue
}

\newif\iflistoffigures
\listoffiguresfalse
\DeclareOption{listoffigures}{
    \listoffigurestrue
}

\newif\ifmastersthesis
\mastersthesisfalse
\DeclareOption{masters}{
    \mastersthesistrue
}

% Pass unrecognized options to the report class
\DeclareOption*{%
    \PassOptionsToClass{\CurrentOption}{report}
}

\ProcessOptions\relax

\LoadClass{report}


% Page layout
% Blindly copied from ogi-thesis.sty, might be out of date

%%% BEGIN %%%
% Top margin is from 1 to 1.5 inches. Bottom margin is no less than 1 inch.
% Page numbers (the ones that live in upper right-hand corner) should be
% 1 inch from the right edge and 0.5 to 1 inch from the top edge. Text
% should begin 0.5 inches after numbers (1 to 1.5 inches from top edge).
% We will place arabic numbers such that their bottoms align at 1 inch
% from the top edge they live and begin text 0.5 inches below them.
\topmargin 0pt
\advance \topmargin by -\headheight
\headsep 0.5in
\textheight 8.4in

% We need 1" margins except on the binding edge, where it is 1 1/2"
% Theses are single-sided, so we don't care about \evensidemargin
% To be extra sure, set right hand margin to 1.1 inches.
\oddsidemargin 0.5in \evensidemargin 0in
\marginparwidth 40pt \marginparsep 10pt
\textwidth 5.9in

% Disallow page breaks at hyphens (this will give some underfull vbox's,
% so an alternative is to use \brokenpenalty=100 and manually search
% for and fix such page breaks)
\brokenpenalty=10000

% Use 1.5 times the normal baseline-to-baseline skip (double space)
\renewcommand{\baselinestretch}{1.5}

% Redefine the macro used for floats (including figures and tables)
% so that single spacing is used.
% (Note \def\figure{\@float{figure}set single spacing} doesn't work
%  because figure has an optional argument)

%\def\@xfloat#1[#2]{%
%   \ifhmode \@bsphack\@floatpenalty -\@Mii\else
%   \@floatpenalty-\@Miii\fi\def\@captype{#1}\ifinner
%      \@parmoderr\@floatpenalty\z@
%    \else\@next\@currbox\@freelist{\@tempcnta\csname ftype@#1\endcsname
%       \multiply\@tempcnta\@xxxii\advance\@tempcnta\sixt@@n
%       \@tfor \@tempa :=#2\do
%                        {\if\@tempa h\advance\@tempcnta \@ne\fi
%                         \if\@tempa t\advance\@tempcnta \tw@\fi
%                         \if\@tempa b\advance\@tempcnta 4\relax\fi
%                         \if\@tempa p\advance\@tempcnta 8\relax\fi
%         }\global\count\@currbox\@tempcnta}\@fltovf\fi
%    \global\setbox\@currbox\vbox\bgroup 
%    \def\baselinestretch{1}\@normalsize
%    \boxmaxdepth\z@
%    \hsize\columnwidth \@parboxrestore}

\let\latex@xfloat=\@xfloat
\def\@xfloat #1[#2]{%
  \latex@xfloat #1[#2]%
  \def\baselinestretch{1}
  \@normalsize\normalsize
  \normalsize
}

% Redefine the macro used for footnotes to use single spacing
\long\def\@footnotetext#1{\insert\footins{\def\baselinestretch{1}\footnotesize
    \interlinepenalty\interfootnotelinepenalty 
    \splittopskip\footnotesep
    \splitmaxdepth \dp\strutbox \floatingpenalty \@MM
    \hsize\columnwidth \@parboxrestore
   \edef\@currentlabel{\csname p@footnote\endcsname\@thefnmark}\@makefntext
    {\rule{\z@}{\footnotesep}\ignorespaces
      #1\strut}}}

% Increase the space between the last line of text and footnote rule.
\skip\footins 20pt plus4pt minus4pt

% Change the l@chapter command. Now this commands uses dotted fills
% for chapter level contentlines in the Table of Contents.
% Change requested by Julianne Williams
\renewcommand\l@chapter[2]{%
  \ifnum \c@tocdepth >\m@ne
    \addpenalty{-\@highpenalty}%
    \vskip 1.0em \@plus\p@
    \setlength\@tempdima{1.5em}%
    \begingroup
      \parindent \z@ \rightskip \@pnumwidth
      \parfillskip -\@pnumwidth
      \leavevmode
      \advance\leftskip\@tempdima
      \hskip -\leftskip
      {\bfseries #1}\nobreak\leaders\hbox{$\m@th \mkern \@dotsep mu.\mkern
	 \@dotsep mu$}\hfill \nobreak
             \hbox to\@pnumwidth{\hss \bfseries #2}\par
      \penalty\@highpenalty
    \endgroup
  \fi}
%%% END %%%


% Single-spaced environment
\def\singlespace{%
    \vskip\parskip
    \vskip\baselineskip
    \def\baselinestretch{1.2}
    \ifx\@currsize\normalsize\@normalsize\else\@currsize\fi
    \vskip-\parskip
    \vskip-\baselineskip
}
\def\endsinglespace{\par}


% Front matter

% Author info
% \author, \title are defined in report.cls
\newcommand{\previousdegrees}[1]{\newcommand{\@previousdegrees}{#1}}
\newcommand{\discipline}[1]{\newcommand{\@discipline}{{#1}}}

% Degree info
\ifmastersthesis
    \newcommand{\thesistype}{thesis}
    \newcommand{\degreetype}{Master of Science}
    \newcommand{\degreeabbreviation}{M.\,S.}
\else
    \newcommand{\thesistype}{dissertation}
    \newcommand{\degreetype}{Doctor of Philosophy}
    \newcommand{\degreeabbreviation}{Ph.\,D.}
\fi
\newcommand{\department}{Center for Spoken Language Understanding}
\newcommand{\school}{School of Medicine}
\newcommand{\university}{Oregon Health \& Science University}
\newcommand{\degreedate}[2]{\newcommand{\@degreemonth}{#1}\newcommand{\@degreeyear}{#2}}

% Thesis advisory committee
\newcommand{\@thesisadvisor}{Thesis Advisor}
\newcommand{\principaladvisor}[2]{\newcommand{\@advisor}{#1}\newcommand{\@advisortitle}{#2}}
\newcommand{\firstreader}[2]{\newcommand{\@firstreader}{#1}\newcommand{\@firstreadertitle}{#2}}
\newcommand{\secondreader}[2]{\newcommand{\@secondreader}{#1}\newcommand{\@secondreadertitle}{#2}}
\newcommand{\thirdreader}[2]{\newcommand{\@thirdreader}{#1}\newcommand{\@thirdreadertitle}{#2}}
\newcommand{\fourthreader}[2]{\newcommand{\@fourthreader}{#1}\newcommand{\@fourthreadertitle}{#2}}
\newcommand{\fifthreader}[2]{\newcommand{\@fifthreader}{#1}\newcommand{\@fifthreadertitle}{#2}}

% Signatures
\newcommand{\signature}[2]{%
    \begin{center}
        \vspace{0.3in}
        \rule{3.0in}{0.4pt} \\
        \begin{singlespace}#1\\#2\end{singlespace}
    \end{center}
}

% Title page
\renewcommand{\titlepage}{%
    \pagenumbering{roman}
    \pagestyle{plain}
    \thispagestyle{empty}
    \def\baselinestretch{1.3}
    \null
    \begin{center}
        \huge\bf\expandafter{\@title}
    \end{center}
    \vfill
    \begin{center}
        \large \rm \@author \\
        \@previousdegrees
    \end{center}
    \vfill
    \begin{center}
        \large Presented to the \\
        \department \\
        within the~\university \\
        \school \\
        in partial fulfillment of \\
        the requirements for the degree \\
        \degreetype \\
        in \\
        \@discipline \\
        \vspace{0.5in}
        \@degreemonth\ \@degreeyear
    \end{center}
    \newpage
}


% Copyright page
% http://www.ohsu.edu/xd/education/library/services/theses-dissertations/your-thesis-and-copyright.cfm
\newcommand{\copyrightpage}{%
    \def\baselinestretch{1.3}
    \null\vfill
    \begin{center}
    	\large
		Copyright \copyright\ 2016 \@author \\
		All rights reserved
	\end{center}
	\vfill\newpage
}


% Certificate of approval page
\newcommand{\signaturepage}{%
    \begin{center}
        \begin{singlespace}
            \department \\
            \school \\
            \university
        \end{singlespace}
        \rule{2.75in}{0.4pt} \\
        \vspace{0.1in}
        CERTIFICATE OF APPROVAL \\
        \vspace{0.02in}
        \rule{2.75in}{0.4pt} \\
        \vspace{0.07in}
        This is to certify that the \degreeabbreviation\ \thesistype\ of \\
        \@author \\
        has been approved. \\
        \vfill
        \signature{\@advisor, \@thesisadvisor}{\@advisortitle}
        \vfill
        \signature{\@firstreader}{\@firstreadertitle}
        \vfill
        \signature{\@secondreader}{\@secondreadertitle}
        \vfill
        \signature{\@thirdreader}{\@thirdreadertitle}
        \vfill
        \ifcsname @fourthreader\endcsname
            \signature{\@fourthreader}{\@fourthreadertitle}
        \fi
    \end{center}
}


% Front matter
\newcommand{\frontmatter}{%
    \pagenumbering{roman}
    \pagestyle{plain}
    \titlepage
    \ifcopyright
	    \copyrightpage
	\fi
    \signaturepage
}   


% Additional preface sections
\newcommand{\prefacesection}[1]{%
    \chapter*{#1}
    \addcontentsline{toc}{chapter}{#1}
}


% Table of contents
\let\oldtableofcontents\tableofcontents
\renewcommand{\tableofcontents}{%
    \begin{singlespace}
    \oldtableofcontents
    \end{singlespace}
    \newpage
    \iflistoftables
        \begin{singlespace}
        \listoftables
        \end{singlespace}
    \fi
    \iflistoffigures
        \begin{singlespace}
        \listoffigures
        \end{singlespace}
    \fi
}


% Abstract
\let\oldabstract\abstract
\renewcommand{\abstract}{%
    \def\@makeschapterhead##1{
        \vspace*{0.25in}
        \begin{center}
            \huge \bf ##1\par
            \nobreak \vskip 40pt
        \end{center}
    }
    \chapter*{Abstract}
    \addcontentsline{toc}{chapter}{Abstract}
    \begin{center}
        \begin{singlespace}
            \large \bf \expandafter{\@title} \\ [0.25in]
            \normalsize \rm \@author \\ [0.25in]
            \degreetype \\
            \department \\
            within the~\university \\
            \school \\ [0.25in]
            \@degreemonth\ \@degreeyear \\
            \@thesisadvisor:\ \@advisor
        \end{singlespace}
    \end{center}
}


% Body
\newcommand{\body}{%
    \newpage
    \pagenumbering{arabic}
    \pagestyle{headings}
    \def\chaptermark##1{}
}


% Biography
\newcommand{\biography}{%
	\def\@makeschapterhead##1{
	    \vspace*{0.2in}{
	        \center 
            \huge \bf ##1\par
	        \nobreak \vskip 40pt }
	    }
	\chapter*{Biographical Note}
	\addcontentsline{toc}{chapter}{Biographical Note}
}


% Additional formatting
% Blindly copied from ogi-thesis.sty, might be out of date
%%% BEGIN %%%
% Redefine \thebibliography to go to a new page and put an entry in the
% Table of Contents
\def\thebibliography#1{%
    \chapter*{Bibliography}
    \list {[\arabic{enumi}]}{\settowidth\labelwidth{[#1]}\leftmargin\labelwidth
    \advance\leftmargin\labelsep \usecounter{enumi} }
    \usecounter{enumi}
    \def\newblock{\hskip .11em plus .33em minus .07em}
    \sloppy\clubpenalty4000\widowpenalty4000
    \sfcode`\.=1000\relax}

% Redefine \thebibliography to not use any page headings except the
% page number.
\let\@ldthebibliography\thebibliography
\renewcommand{\thebibliography}[1]{
	\newpage
	\addcontentsline{toc}{chapter}{Bibliography}
	\@ldthebibliography{#1}
}


% Start out normal
\pagestyle{headings}

% Redefine \@makeschapterhead and \@makechapterhead so they start
% out at the top of the page and used \huge rather than \Huge font sizes.
\def\@makeschapterhead#1{%
    \vspace*{0.2in}{%
        \center 
        \huge \bf #1\par
        \nobreak \vskip 40pt
    }
}
\def\@makechapterhead#1{%
    \vspace*{0.2in}{%
        \center
        \ifnum \c@secnumdepth >\m@ne \huge\bf \@chapapp{} \thechapter \par
        \vskip 20pt \fi \huge \bf #1\par
        \nobreak \vskip 40pt
    }
}
%%% END %%%
