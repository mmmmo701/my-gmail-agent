from enum import IntEnum, auto

# main

class Constants(IntEnum):
    # main
    NO_UNREAD = 0
    CLASSIFYING = auto()
    GENERATING_EVENT = auto()
    EVENT_CREATED = auto()
    EVENT_ADDED = auto()


class TextIO:
    def __init__(self):
        self.msg = [
            # main
            "No unread emails.",
            "Classifying emails...",
            "Generating Calendar Event...",
            "Event created successfully. Now adding events to your Google Calendar.",
            "Event added successfully.",
        ]



    # Display a string to the user
    
    def show_str(self, s):
        print(s)

    def show_msg(self, x):
        if 0 <= x < len(self.msg):
            self.show_str(self.msg[x])
        else:
            print(f"Message index {x} not found")

    def show_formatted_msg(self, x, **kwargs):
        if 0 <= x < len(self.msg):
            self.show_str(self.msg[x].format(**kwargs))
        else:
            print(f"Message index {x} not found")

    def show_categorized_email(self, category, subject):
        print(f"[{category}] {subject}")
    
    def show_event(self, ics_string):
        print("-----BEGIN ICS EVENT-----")
        print(ics_string)
        print("-----END ICS EVENT-----")


    def show_error(self, error_msg):
        print(f"Error: {error_msg}")



    # Display cover art or welcome message

    def show_cover(self):
        cover_text = """
        ╔════════════════════════════════════════╗
        ║             GMAIL AGENT                ║
        ║             Welcome                    ║
        ╚════════════════════════════════════════╝
        """
        print(cover_text)
    
