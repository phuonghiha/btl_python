class Animation:

    def __init__(self, frames, fps=8, loop=True):
        self.frames = frames
        self.fps = fps
        self.loop = loop

        self.current_frame = 0
        self.timer = 0
        self.finished = False

    def reset(self):
        self.current_frame = 0
        self.timer = 0
        self.finished = False

    def update(self, dt):
        if self.finished:
            return

        if len(self.frames) <= 1:
            return

        self.timer += dt

        frame_time = 1 / self.fps

        while self.timer >= frame_time:
            self.timer -= frame_time
            self.current_frame += 1

            if self.current_frame >= len(self.frames):

                if self.loop:
                    self.current_frame = 0

                else:
                    self.current_frame = len(self.frames) - 1
                    self.finished = True
                    break

    def get_current_frame(self):
        return self.frames[self.current_frame]