v1.1.0 (14-09-2020)
------

Major changes:

- tool 2. a1 to a4 deleted and integrated in new tool named a1. 'Punten op lijnen maken'. 
  This integrated tool draws points on lines based on distance, percentage, interval, count, start- end nodes 
  including random points. 
- tool 2. a2 (new tool) developed to calculate distance of points on a line
- tool 2. a3 (new tool) developed to interpolate values between points (e.g. new profiles based on old profiles)
- tool 3. d2 'genereer wdb bestanden' verwijderd. Wdb kan al in de server gemaakt worden. 
- deleted tool z8 (0. b2 fotonamen naar kolommen)). Tool was obsolete.
- changed old names z1-z8 and individual tool names to better structure the toolbox. 

Known issues:
- tool 2e1, 3a1 and 3b3 sometimes give 'cannot decode utf-8' error. To fix this, restart ArcMap.
- all tools sometimes give the 'cannot add to display' error. To fix this, restart ArcMap. 
- Tool 1 b2. check metfile op fouten does not work if openpyxl library is not installed. 



v1.0.0 (till 13-09-2020)
------

Original toolbox optimized for ArcMap 10.4.