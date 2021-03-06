import so3g
from spt3g import core
import time
import os
import binascii


class HKSessionHelper:
    def __init__(self, session_id=None, start_time=None,
                 description='No description provided.'):
        """Helper class to produce G3Frame templates for creating streams of
        generic HK data.

        Arguments:
          session_id: an integer session ID for the HK session.  If
            not provided (recommended) then it will be generated based
            on the PID, the start_time, and the description string.
          start_time (float): a timestamp to use for the HK session.
          description (str): a description of the agent generating the
            stream.
        """
        if start_time is None:
            start_time = time.time()
        self.start_time = start_time
        self.description = description
        self.provs = {}
        self.next_prov_id = 0
        if session_id is None:
            session_id = self._generate_session_id(start_time, description)
        self.session_id = session_id

    @staticmethod
    def _generate_session_id(timestamp=None, description=''):
        if timestamp is None:
            timestamp = time.time()
        if description is None:
            description = '?'
        # Bit-combine some unique stuff.  It's useful if this sorts in
        # time, so lead off with the timestamp.
        elements = [(int(timestamp), 32),
                    (os.getpid(), 14),
                    (binascii.crc32(bytes(description, 'utf8')), 14)]
        session_id = 0
        for i, b in elements:
            session_id = (session_id << b) | (i % (1 << b))
        return session_id

    def add_provider(self, description='No provider description... provided'):
        prov_id = self.next_prov_id
        self.next_prov_id += 1
        self.provs[prov_id] = {'description': description}
        return prov_id

    def remove_provider(self, prov_id):
        del self.provs[prov_id]

    """
    Frame generators.
    """

    def session_frame(self):
        """
        Return the Session frame.  No additional information needs to be
        added to this frame.  This frame initializes the HK stream (so
        it should be the first frame of each HK file; it should
        precede all other HK frames in a network source).
        """
        f = core.G3Frame()
        f.type = core.G3FrameType.Housekeeping
        f['hkagg_type'] = so3g.HKFrameType.session
        f['session_id'] = self.session_id
        f['start_time'] = self.start_time
        f['description'] = self.description
        return f

    def status_frame(self, timestamp=None):
        """
        Return a Status frame template.  Before processing, the session
        manager should update with information about what providers
        are currently connected.
        """
        if timestamp is None:
            timestamp = time.time()
        f = core.G3Frame()
        f.type = core.G3FrameType.Housekeeping
        f['hkagg_type'] = so3g.HKFrameType.status
        f['session_id'] = self.session_id
        f['timestamp'] = timestamp
        provs = core.G3VectorFrameObject()
        for prov_id in sorted(self.provs.keys()):
            prov = core.G3MapFrameObject()
            prov['prov_id'] = core.G3Int(prov_id)
            prov['description'] = core.G3String(
                self.provs[prov_id]['description'])
            provs.append(prov)
        f['providers'] = provs
        return f

    def data_frame(self, prov_id, timestamp=None):
        """
        Return a Data frame template.  The prov_id must match the prov_id
        in one of the Provider blocks in the preceding status frame.
        The session manager should create and add IrregBlockDouble items
        to the 'blocks' list.
        """
        if timestamp is None:
            timestamp = time.time()
        f = core.G3Frame()
        f.type = core.G3FrameType.Housekeeping
        f['hkagg_type'] = so3g.HKFrameType.data
        f['session_id'] = self.session_id
        f['prov_id'] = prov_id
        f['timestamp'] = timestamp
        f['blocks'] = core.G3VectorFrameObject()
        return f
