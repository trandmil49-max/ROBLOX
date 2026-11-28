# Story file format

Plain UTF-8 text. Lines starting with `#` are comments.

```
LANG: en                      # tr | en | es | fr | ar
QUALITY: final                # optional: final (1080p60) | draft | test
CAST:
Max | teen | skin=peach | hair=spiky,black | top=green | outfit=jacket | top2=yellow | bottom=jeans | acc=glasses
SHOTS:
street@day | wide/push | *Max=happy:walk | props=dog :: Every evening, Max walked his dog
```

## Cast line
`Name | body | key=value | ...`

* body: `kid boy girl teen man woman old granny baby big`
* skin: `light pale peach tan brown dark yellow green blue grey` (or `#rrggbb`)
* hair: `style,color` - styles: `short messy spiky curly afro long bob ponytail bun cap bald`; colors: `black brown darkbrown blonde ginger white grey red blue pink green purple`
* outfit: `tee hoodie jacket suit dress dress_short apron`; pattern: `plain stripes plaid knit`; `top`, `top2`, `bottom`, `shoes` colors
* acc (comma separated): `glasses mustache beard freckles beanie crown backpack headphones cape tie labcoat`

## Shot line
`location[@time] | camera[/move] | characters | props :: narration`

* location: `street city park forest mountain beach house living_room bedroom kitchen classroom shop office basement underwater`
  (aliases: school, home, store, downtown, garden ...)
* time: `day dawn dusk night overcast dark` (indoor places ignore it)
* camera: `wide establish medium closeup extreme low high over dutch insert`; move: `push pull pan orbit handheld static`
* characters: `Name=expression:action`, `*` marks the focus character, `A>B` changes expression mid-shot
  * expressions: neutral happy grin laugh sad cry angry furious surprised shocked scared worried sleepy smirk wink love dizzy disgusted evil embarrassed thinking excited tired serious
  * actions: idle talk listen walk walk_l run run_l sneak approach leave wave point shock laugh cry sad angry jump celebrate sit think fall sleep hug shrug scared dance eat drink type look knock push pull hide
* props: `cabinet computer laptop phone headphones tv bed sofa table chair desk lamp door fridge bookshelf book backpack pizza burger cake apple coffee money coin gift trophy ball balloon flower plant clock mirror bag umbrella key chest pumpkin icecream bottle car dog cat puppy bird ghost monster tree pine bench rocket`
* narration: exactly the words the voice actor speaks for this shot (3-6 words works best)

Objects named in the narration are shown automatically even if they are not listed in `props`.
Every camera angle lasts at most 2 seconds; longer shots are cut automatically with new angles.
