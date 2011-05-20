/* sslice - Take a screenshot of a selected area of the screen.
   Copyright (C) 2009 Lucas Alvares Gomes <lucasagomes@gmail.com>.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>. */

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <getopt.h>
#include <X11/Xlib.h>
#include <X11/cursorfont.h>
#include <gdk/gdk.h>

static struct option const long_options[] =
{
  {"output", required_argument, 0, 'o'},
  {"type", required_argument, 0, 't'},
  {"help", no_argument, 0, 'h'},
  {0, 0, 0, 0}
};

/* Functions */
int select_screen(int *width, int *height, int *x, int *y);
int get_screenshot(char *output, char *type, int width, int height, int x, int y);
void usage();

int main(int argc, char** argv)
{
    char *output = "screenshot";
    char *type = "png";
    const char types[][5] = {"png", "jpeg", "tiff", "bmp"};
    int index, c, ret;
    int width, height, x, y;
    int i = 0, val_type = 0;

    /* Checking the arguments */
    while (1){
        int option_index = 0;
        c = getopt_long(argc, argv, "o:t:h", long_options, &option_index);

        if (c == -1)
            break;

        switch (c)
        {
        case 'o':
            output = optarg;
            break;
        case 't':
            type = optarg;
            break;
        case 'h':
            usage();
            return 0;
        default:
            exit(-1);
        }
    }

    for (index = optind; index < argc; index++){
        fprintf(stderr, "Non-option argument %s.\n", argv[index]);
        exit(-1);
    }

    /* Checking the type */
    for (i=0; i < sizeof(types)/sizeof(types[0]); i++){
        if (strcmp(types[i], type) == 0){
            val_type=1;
        }
    }

    if (!val_type){
        fprintf(stderr, "Invalid type. Valid types are png, jpeg, tiff or bmp.\n");
        exit(-1);
    }

    /* Select the screen area */
    gdk_init(&argc, &argv);
    ret = select_screen(&width, &height, &x, &y);

    if (ret != 0){
        fprintf(stderr, "Cannt capture screen.");
        exit(1);
    }

    /* Get and save the screenshot */
    ret = get_screenshot(output, type, width, height, x, y);
    if (ret != 0){
        fprintf(stderr, "Cannt save the screenshot.");
        exit(1);
    }

}

int select_screen(int *width, int *height, int *x, int *y){
    int sel_x = 0, sel_y = 0, sel_w = 0, sel_h = 0;
    int rect_x = 0, rect_y = 0, rect_w = 0, rect_h = 0;
    int done = 0;

    XEvent ev;
    Display *disp = XOpenDisplay(NULL);

    if(!disp){
        fprintf(stderr, "Cannt get the display.\n");
        return -1;
    }

    Screen *scr = NULL;
    scr = ScreenOfDisplay(disp, DefaultScreen(disp));

    Window root = 0;
    root = RootWindow(disp, XScreenNumberOfScreen(scr));

    Cursor cursor_arrow, cursor_angle;
    cursor_arrow = XCreateFontCursor(disp, XC_left_ptr);
    cursor_angle = XCreateFontCursor(disp, XC_lr_angle);

    XGCValues gcval;
    gcval.function = GXxor;
    gcval.subwindow_mode = IncludeInferiors;

    GC gc;
    gc = XCreateGC(disp, root,
                   GCFunction|GCForeground|GCBackground|GCSubwindowMode,
                   &gcval);

    if ((XGrabPointer(disp, root, False,
        ButtonMotionMask|ButtonPressMask|ButtonReleaseMask, GrabModeAsync,
        GrabModeAsync, root, cursor_arrow, CurrentTime) != GrabSuccess)){
        fprintf(stderr, "Fail grabbing the pointer.\n");
        return -1;
    }

    while (!done){
        XNextEvent(disp, &ev);
        switch (ev.type){
            case MotionNotify:
                /* Re-draw rectangle */
                if (rect_w || rect_h)
                    XDrawRectangle(disp, root, gc, rect_x, rect_y, rect_w, rect_h);

                rect_x = sel_x;
                rect_y = sel_y;
                rect_w = ev.xmotion.x - rect_x;
                rect_h = ev.xmotion.y - rect_y;

                if (rect_w < 0) {
                    rect_x += rect_w;
                    rect_w = 0 - rect_w;
                }
                if (rect_h < 0) {
                    rect_y += rect_h;
                    rect_h = 0 - rect_h;
                }

                /* Draw the rectangle */
                XDrawRectangle(disp, root, gc, rect_x, rect_y, rect_w, rect_h);
                XFlush(disp);
                break;
            case ButtonPress:
                sel_x = ev.xbutton.x;
                sel_y = ev.xbutton.y;
                break;
            case ButtonRelease:
                done = 1;
                break;
        }
    }

    XDrawRectangle(disp, root, gc, rect_x, rect_y, rect_w, rect_h);

    sel_w = (ev.xbutton.x - sel_x);
    sel_h = (ev.xbutton.y - sel_y);

    if (sel_w < 0) {
        sel_x += sel_w;
        sel_w = 0 - sel_w;
    }
    if (sel_h < 0) {
        sel_y += sel_h;
        sel_h = 0 - sel_h;
    }
    sel_w += 1;
    sel_h += 1;

    /* Fill vars */ 
    *width = sel_w;
    *height = sel_h;
    *x = sel_x;
    *y = sel_y;

    XFlush(disp);
    XCloseDisplay(disp);

    return 0;
}

int get_screenshot(char *output, char *type, int width, int height, int x, int y){
    int ret;

    GdkWindow* window = window = gdk_get_default_root_window();
    GdkPixbuf* screenshot = gdk_pixbuf_get_from_drawable(NULL, window, NULL,
                                                          x, y, 0, 0, width, height);
    GError* error = NULL;
    ret = gdk_pixbuf_save(screenshot, output, type, &error, NULL);
    if (!ret)
        return -1;
    return 0;
}

void usage(){
    printf("Options:\n\
  -o, --output           Save to OUTPUT FILE. The default is 'screenshot'.\n\
  -t, --type             png, jpeg, tiff or bmp. The default is png.\n\n");
}
