Tan Lines history files (hist-a.js, hist-b.js, hist-careers.js, hist-itf0..11.js, hist-itfl0..11.js, hist-chart.js, hist-pts.js)

Derived from Jeff Sackmann's WTA match, ranking and player database (https://github.com/JeffSackmann,
Tennis Abstract), licensed CC BY-NC-SA 4.0: https://creativecommons.org/licenses/by-nc-sa/4.0/

Changes made: tour-level matches only, columns trimmed, player ids joined to ESPN's where the
player is active, and per-player career summaries and Elo ratings computed by history.py.

hist-itf0..11.js and hist-itfl0..11.js (sharded by player id): ITF, WTA 125 and qualifying matches (wta_matches_qual_itf_*.csv in the
same database), kept for players with a career entry and shown apart from the tour-level record.

hist-chart.js and hist-pts.js: from the Match Charting Project (Jeff Sackmann / Tennis Abstract,
https://github.com/JeffSackmann/tennis_MatchChartingProject), volunteer-charted women's matches,
licensed CC BY-NC-SA 4.0. Changes made: per-player rates and match lists, and each match's totals
and point sequence re-encoded compactly (one character per point). Not every match is charted.

These derived files are shared under the same licence. Non-commercial use only.
