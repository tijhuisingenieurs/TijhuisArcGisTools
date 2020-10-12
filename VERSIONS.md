v1.1.0 (12-10-2020)
------

Major changes:

- tool 2. a1 to a4 deleted and integrated in new tool named a1. 'Punten op lijnen maken'. 
  This integrated tool draws points on lines based on distance, percentage, interval, count, start- end nodes 
  including random points. 
- tool 2. a2 (new tool) developed to calculate distance of points on a line
- tool 2. a3 (new tool) developed to interpolate values between points (e.g. new profiles based on old profiles)
- tool 3. d2 'genereer wdb bestanden' verwijderd. Wdb kan al in de server gemaakt worden. 
- deleted tool z8 (0. b2 fotonamen naar kolommen)). Tool was obsolete.
- Removed old example data (was cluttered) and added 'testdata' folder, which contains input data for each tool,
  as well as expected outcomes of each tool. 
- Added script to each tool in order to run said tools without using ArcMap. All tools are directly connected
  to the example data folder.
- Added archive folder for obsolete tools. 

Minor changes
- changed old names z1-z8 and individual tool names to better structure the toolbox. 
- tool 1. a3 column 'Id' deleted.
- tool 2. b1 display file with unused route points changed to optional (checkbox)
- tool 2. b2. added tolerance option (default 0 meter) to snap points to line in case points to not intersect. 
- tool 2. c1. added warning when both fields for 'haakse lijnen' are left empty. 

Bug fixes:
- tool 1. a2 'cleanen van lijnen' split lines error fix. 
- tool 1. b1 sludge and solid soil calculations reversed. Was z2z1, now is z1z2.
- tool 1. b2 gave 'missing Openpyxl library' error. Instructions added to toolbox on how to install openpyxl.
          See 'README.md').
- tool 2. d1 and 2. d2. Fixed issues with iterating through geometry, which caused an error.  
- tool 3. e1 sludge and solid soil calculations reversed. Was z2z1, now is z1z2.
          
Known issues:
- tool 2e1, 3a1 and 3b3 sometimes give 'cannot decode utf-8' error. To fix this, restart ArcMap.
- all tools sometimes give the 'cannot add to display' error. To fix this, restart ArcMap. 
- Tool 1 b2. check metfile op fouten does not work if openpyxl library is not installed. 
- Tools regularly crash when using ArcMap 10.4.1. in Windows 10 environment. 
  Suggested to update ArcMap to 10.7. when using Windows 10. 

v1.0.0 (till 13-09-2020)
------

Original toolbox. 