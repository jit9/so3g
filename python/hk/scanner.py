import so3g
from spt3g import core
import numpy as np

class HKScanner:
    """Module that scans and reports on HK archive contents and compliance.
    
    Attributes:
      stats (dict): A nested dictionary of statistics that are updated as
        frames are processed by the module.  Elements:

        - ``n_hk`` (int): The number of HK frames encountered.
        - ``n_other`` (int): The number of non-HK frames encountered.
        - ``n_session`` (int): The number of distinct HK sessions
          processed.
        - ``concerns`` (dict): The number of warning (key ``n_warning``)
          and error (key ``n_error``) events encountered.  The detail
          for such events is logged to ``spt3g.core.log_warning`` /
          ``log_error``.
    """
    def __init__(self):
        self.session_id = None
        self.providers = {}
        self.stats = {
            'n_hk': 0,
            'n_other': 0,
            'n_session': 0,
            'concerns': {
                'n_error': 0,
                'n_warning': 0
            },
        }

    def report_and_reset(self):
        core.log_info('Report for session_id %i:\n' % self.session_id +
                      str(self.stats) + '\n' +
                      str(self.providers) + '\nEnd report.',
                      unit='HKScanner')
        self.session_id = None

    def __call__(self, f):
        """Processes a frame.  Only Housekeeping frames will be examined;
        other frames will simply be counted.  All frames are passed
        through unmodified.

        """
        if f.type == core.G3FrameType.EndProcessing:
            self.report_and_reset()
            return [f]

        if f.type != core.G3FrameType.Housekeeping:
            self.stats['n_other'] += 1
            return f

        self.stats['n_hk'] += 1

        if f['hkagg_type'] == so3g.HKFrameType.session:
            session_id = f['session_id']
            if self.session_id is not None:
                if self.session_id != session_id:
                    self.report_and_reset()  # note this does clear self.session_id.
            if self.session_id is None:
                core.log_info('New HK Session id = %i, timestamp = %i' %
                              (session_id, f['start_time']), unit='HKScanner')
                self.session_id = session_id
                self.stats['n_session'] += 1

        elif f['hkagg_type'] == so3g.HKFrameType.status:
            # Have any providers disappeared?
            now_prov_id = [p['prov_id'].value for p in f['providers']]
            for p, info in self.providers.items():
                if p not in now_prov_id:
                    info['active'] = False
            
            # New providers?
            for p in now_prov_id:
                info = self.providers.get(p)
                if info is not None:
                    if not info['active']:
                        core.log_warn('prov_id %i came back to life.' % p,
                                      unit='HKScanner')
                        self.stats['concerns']['n_warning'] += 1
                        info['n_active'] += 1
                        info['active'] = True
                else:
                    self.providers[p] = {
                        'active': True, # Currently active (during processing).
                        'n_active': 1,  # Number of times this provider id became active.
                        'n_frames': 0,  # Number of data frames.
                        'timestamp_init': f['timestamp'],  # Timestamp of provider appearance
                        'timestamp_data': None, # Timestamp of most recent data frame.
                        'ticks': 0,   # Total number of timestamps in all blocks.
                        'span': None, # (earliest_time, latest_time)
                    }

        elif f['hkagg_type'] == so3g.HKFrameType.data:
            info = self.providers[f['prov_id']]
            info['n_frames'] += 1
            t_this = f['timestamp']
            if info['timestamp_data'] is None:
                t_ref = info['timestamp_init']
                if t_this < t_ref:
                    core.log_warn('data timestamp (%.1f) precedes provider '
                                  'timestamp by %f seconds.' % (t_this, t_this - t_ref),
                                  unit='HKScanner')
                    self.stats['concerns']['n_warning'] += 1
            elif t_this <= info['timestamp_data']:
                core.log_warn('data frame timestamps are not strictly ordered.',
                              unit='HKScanner')
                self.stats['concerns']['n_warning'] += 1
            info['timestamp_data'] = t_this # update

            t_check = []
            for b in f['blocks']:
                if len(b.t):
                    if info['span'] is None:
                        info['span'] = b.t[0], b.t[-1]
                    else:
                        t0, t1 = info['span']
                        info['span'] = min(b.t[0], t0), max(b.t[-1], t1)
                    t_check.append(b.t[0])
                info['ticks'] += len(b.t)
                for k,v in b.data.items():
                    if len(v) != len(b.t):
                        core.log_error('Field "%s" has %i samples but .t has %i samples.' %
                                       (k, len(v), len(b.t)))
                        self.stats['concerns']['n_error'] += 1
            if len(t_check) and abs(min(t_check) - t_this) > 60:
                core.log_warn('data frame timestamp (%.1f) does not correspond to '
                              'data timestamp vectors (%s) .' % (t_this, t_check),
                              unit='HKScanner')
                self.stats['concerns']['n_warning'] += 1
                
        else:
            core.log_warn('Weird hkagg_type: %i' % f['hkagg_type'],
                          unit='HKScanner')
            self.stats['concerns']['n_warning'] += 1

        return [f]

if __name__ == '__main__':
    # Run me on a G3File containing a Housekeeping stream.
    core.set_log_level(core.G3LogLevel.LOG_INFO)
    import sys
    for f in sys.argv[1:]:
        p = core.G3Pipeline()
        p.Add(core.G3Reader(f))
        p.Add(HKScanner())
        p.Run()
