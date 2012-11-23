#!/usr/bin/python
import gtk
import vte
import os
import signal

class MainWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.connect("delete-event", self.main_quit)
        self.vte = vte.Terminal()
        self.set_position(gtk.WIN_POS_CENTER)
        self.vte.connect("child-exited", self.command_executed)
        self.vte.connect("eof", self.command_executed)
        self.connect("key-press-event", self.clear)
        self.vte.connect_after("expose-event", self.do_paint)
        self.add(self.vte)
        self.pid = self.vte.fork_command(command = 'bash')
        self.pipe_name = "/tmp/pipe_show_%s" % str(self.pid)
        self.initial = "/tmp/show_gppid_%s"  % str(self.pid)
        with open(self.initial, "w+") as f:
             f.write(str(os.getpid()))
        self.loader = gtk.gdk.PixbufLoader()
        self.pixbuf = None

    def main_quit(self, widget, window):
       try:
          self.loader.close()
       except:
          pass
       self.remove_pipe()
       self.remove_gpid()
       gtk.main_quit()

    def remove_gpid(self):
      try:
        os.unlink(self.initial)
      except:
        pass

    def remove_pipe(self):
      try:
        os.unlink(self.pipe_name)
      except:
        pass

    def clear(self, widget, event):
       keyname = gtk.gdk.keyval_name(event.keyval)
       if not self.pixbuf is None:
          column, row = self.vte.get_cursor_position()
          if (column == self.vte.get_column_count() - 1) or ("Control_L" == keyname):
             self.pixbuf = None
             self.vte.realize()
             realized = True
       if "Return" == keyname:
          if not self.pixbuf is None:
             self.pixbuf = None
             self.vte.realize()
       return False

    def preprocess_show(self):
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
            do = self.loader.close()
        except:
             pass
        if not pipe.closed: pipe.close()
        self.remove_pipe()
        if do:
           self.do_show()
        self.loader = gtk.gdk.PixbufLoader()
        return True

    def do_show(self):
        try:
           pixbuf = self.loader.get_pixbuf()
        except:
           return False

        x, y, width, height = self.vte.get_allocation()
        lines = "".join(["\n" for x in xrange(0, self.vte.get_row_count() - 1)])
        self.vte.feed(lines)

        image_width, image_height = pixbuf.get_width(), pixbuf.get_height()
        if image_width > width:
           image_height = int(image_height * width / image_width)
           image_width  = width
        if image_height > (height - self.vte.get_char_height() - 10):  # 10 is for better fitness...
           image_width  = int(image_width * (height - self.vte.get_char_height() - 10) / image_height)
           image_height = height - self.vte.get_char_height() - 10

        self.pixbuf = pixbuf.scale_simple(image_width, image_height, gtk.gdk.INTERP_BILINEAR)
        self.vte.window.draw_pixbuf(self.get_style().white_gc, \
                                    self.pixbuf, \
                                    0, 0, 0, 0, image_width, image_height)
        return True

    def do_paint(self, widget, window):
       if self.pixbuf is not None:
          self.vte.window.draw_pixbuf(self.get_style().white_gc, \
                                      self.pixbuf, \
                                      0, 0, 0, 0, \
                                      self.pixbuf.get_width(), \
                                      self.pixbuf.get_height())
       return False

    def command_executed(self, terminal):
        self.main_quit(self.vte, self.vte.window)

    def SIGUSR_handler(self, signum, frame):
        self.preprocess_show()

main_win = MainWindow()
signal.signal(signal.SIGUSR1, main_win.SIGUSR_handler)
main_win.show_all()
gtk.main()
