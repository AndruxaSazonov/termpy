#!/usr/bin/python
import gtk
import vte
import os

class DrawableVTE(vte.Terminal, gtk.DrawingArea):
    def __init__(self):
        vte.Terminal.__init__(self)
        gtk.DrawingArea.__init__(self)

class MainWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.connect("delete-event", self.main_quit)
        self.vte = DrawableVTE()
        self.vte.connect("child-exited", self.command_executed)
        self.vte.connect("eof", self.command_executed)
        self.connect_after("key-release-event", self.keypressed)
        self.vte.connect_after("expose-event", self.do_paint)
        self.add(self.vte)
        self.pid = self.vte.fork_command(command = 'bash')
        self.pipe_name = "/tmp/pipe_show_%s" % str(self.pid)
        self.loader = gtk.gdk.PixbufLoader()
        self.pixbuf = None

    def main_quit(self, widget, window):
       try:
          self.loader.close()
       except:
          pass
       self.remove_pipe()
       gtk.main_quit()

    def remove_pipe(self):
      try:
        os.unlink(self.pipe_name)
      except:
        pass

    def keypressed(self, widget, event):
        self.pixbuf = None
        if event.keyval == 65293: # enter key
             if not os.path.exists(self.pipe_name):
                return False
             try:
               pipe = open(self.pipe_name, "rb")
             except:
               self.remove_pipe()
               return False
             if not pipe:
                self.remove_pipe()
                return False
             for line in pipe:
                self.loader.write(line)
             do = False
             try:
                self.loader.close()
                do = True
             except:
                pass
             if not pipe.closed: pipe.close()
             self.remove_pipe()
             if do: self.do_show()
             self.loader = gtk.gdk.PixbufLoader()
        return False

    def do_show(self):
        x, y, width, height = self.vte.get_allocation()
        column, row = self.vte.get_cursor_position()

        spaces_number =  self.vte.get_column_count() - column 
        spaces_number += self.vte.get_column_count()*self.vte.get_row_count() 
        spaces = "".join([" " for x in xrange(0, spaces_number)])
        try:
           pixbuf = self.loader.get_pixbuf()
        except:
           return False
        self.vte.feed(spaces)
        image_width, image_height = pixbuf.get_width(), pixbuf.get_height()

        if image_width > width:
           image_height = int(image_height * width / image_width)
           image_width  = width
        if image_height > (height - self.vte.get_char_height() - 8):  # 8 is for better fitness...
           image_width  = int(image_width * height / (image_height - self.vte.get_char_height() - 8))
           image_height = height - self.vte.get_char_height() - 8

        self.pixbuf = pixbuf.scale_simple(image_width, image_height, gtk.gdk.INTERP_BILINEAR)
        self.vte.window.draw_pixbuf(self.get_style().white_gc, \
                                    self.pixbuf, \
                                    0, 0, 0, 0, image_width, image_height)
        return False

    def do_paint(self, widget, window):
       if self.pixbuf is not None:
          self.vte.window.draw_pixbuf(self.get_style().white_gc, \
                                      self.pixbuf, \
                                      0, 0, 0, 0, \
                                      self.pixbuf.get_width(), \
                                      self.pixbuf.get_height())
       return False

    def command_executed(self, terminal):
        gtk.main_quit()

main_win = MainWindow()
main_win.show_all()
gtk.main()
