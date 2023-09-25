# Django front end for olympus

## Guide to creating imagery for proper display under a full-srceen responsive set-up

For the latest release, imagery concepts have shifted to the use of the CSS
features *min-aspect-ratio* and *max_aspect-ratio*. These are combined with
*min-width* and *max-width* to produce an image approximating the aspect
ratio of a screen, with an examination of width used to save bandwidth
by delivering a smaller number of pixels where applicable. The breakpoint
for width is always at 1279/1280 pixels.

Aspect ratios were chosen to approximate those in common use, both in
device screens and venues.

### Aspect ratio break points

* 21:9 or wider
* 19:10
* 17.7:10
* 4:3 (from 1:1)
* 3:4 (to 1:1)
* 10:17.7
* 10:19
* 9:21 or narrower

These break points lead to 16 versions of an image, with each image having another whose
aspect ratio is its inverse.

These ratios are occasionally altered: for example, to produce an image that
will scroll rather than fit to the screen. In this example, a 10% addition is made to
the *height* of the image. Aspect ratios in comments are adjusted to reflect this type
of change.

A typical CSS entry for a set of four such images is as follows. In this example, the first
image at 19:10 has an inverse at 10:19. The second image is like the first but is only 1280
pixels wide compared to 2560 pixels for the first. Note the comments and naming conventions.
The numbers used in the name represent the overall aspect ratio and the size of the longest
dimension.

```
.blog_background {
<!-- ... -->
  // 19:10 to 21:9
  @media screen and (min-aspect-ratio: 1.9/1) and (max-aspect-ratio: 2.36999/1) and (min-width: 1280px) {
    // 2560 x 1348
    background-image:url("/static/apps/welcome/image/Paranal_Zodiacal_Light_190_100_2560.jpg");
  }
  @media screen and (min-aspect-ratio: 1.9/1) and (max-aspect-ratio: 2.36999/1) and (max-width: 1279px) {
    // 1280 x 674
    background-image:url("/static/apps/welcome/image/Paranal_Zodiacal_Light_190_100_1280.jpg");
  }
<!-- ... -->
  // 9:21 to 10:19
  @media screen and (min-aspect-ratio: 1/2.37) and (max-aspect-ratio: 1/1.9001) and (min-height: 1280px) {
    // 1348 x 2560
    background-image:url("/static/apps/welcome/image/Zodiacal_Light_Paranal_100_190_2560.jpg");
  }
  @media screen and (min-aspect-ratio: 1/2.37) and (max-aspect-ratio: 1/1.9001) and (max-height: 1279px) {
    // 674 x 1280
    background-image:url("/static/apps/welcome/image/Zodiacal_Light_Paranal_100_190_1280.jpg");
  }
<!-- ... -->
}
```
