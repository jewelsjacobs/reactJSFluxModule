GUI
===

DEV NOTES
*********

Using Popovers
^^^^^^^^^^^^^^
The element which triggers a popover (probably a button) needs the following attributes:

- Class property "rs-popover-source"
- data-popover="<id of the popover element>"
- data-popover-target="<id of the targeted element for the popover>"
- data-popover-position="<the position the popover will appear relative to the target (right, left, bottom-right, bottom-left)>"

The data popover itself needs the following attributes:

- Class properties "rs-popover" and "invisible".
- An id corresponding to the popover source data-popover value.
