# Django front end for olympus

## Guide to organizing imagery for proper display under a responsive set-up

Use the following resolution guide when editing images. All the listed resolutions need to be tested and verified.

Inverses exist to account for horizontal and vertical orientations of mobile devices.

The intent is to use midpoint sizes for related common screen resolutions. This should limit the number of required images and keep responsive cropping to a minimum.

Sizes are calculated by taking simple averages of the grouped resolutions.

A placeholder is used to simplify css conditionals, giving at least two height options at each major width break point (320, 640, 992, 1280, 1920).

```
Target resolutions              Target image dimensions
******************              ***********************

                                             Matched proportions
320                             Full screen  (for inverses)       Mid-point
---                             -----------  -------------------  ---------

a. 480 x 320 (inverse of "c.")  524 x 320    524 x 858            524 x 589
b. 568 x 320 (inverse of "d.")  ...          ...                  ...

c. 320 x 480                    320 x 524
d. 320 x 568                    ... 

e. 360 x 640                    420 x 720
f. 480 x 800                    ...     

640
---

g. 640 x 360 (inverse of "e.")  720 x 420    720 x 1234           720 x 827
h. 800 x 480 (inverse of "f.")  ...          ...                  ...

i. 768 x 1024                   752 x 1194
j. 720 x 1280                   ...
k. 768 x 1280                   ...

992
---

l. 1024 x 768 (inverse of "i.") 1194 x 752   1194 x 1896          1194 x 1324
m. 1024 x 1280 (placeholder)    1024 x 1280

1280
----

m. 1280 x 720 (inverse of "j.") 1340 x 789   1340 x 2128          1340 x 1458
n. 1280 x 768 (inverse of "k.") ....         ....                 ....
o. 1360 x 768                   ....
p. 1440 x 900                   ....

q. 1280 x 1024                  1480 x 1038
r. 1680 x 1050                  ....

1920
----

s. 1920 x 1080                  1920 x 1140
t. 1920 x 1200                   
```
