# Experiments at Pick My Costume

This folder is the site's memory for every bet we've placed. The rule is
simple: before anything ships as an experiment, it gets an entry in
[LEDGER.md](LEDGER.md) stating the hypothesis, the assumptions underneath
it, and the metric movement we project. After it's decided, the entry gets
closed out with what actually happened versus what we projected. A shipped
change with green tests but no stranger traffic is a *bet placed*, not a
*bet won* — the ledger exists so we never confuse the two, and so a cold
reader can see the whole history of what we tried and what we learned.

The ledger opens with a "Holistic read": which of our standing assumptions
the experiments have confirmed, which they've challenged, and which are
still untested. Every 10th closed experiment (or monthly) triggers a review
that rewrites that section from the latest batch. Entries use plain-English
names first — "share-message wording test," not "E-whatever" — with
internal codes in parentheses for traceability. Defect fixes close on
verification; bets close on data or on an explicit judgment call, never on
"it shipped." If the instrumentation behind a metric can't be trusted, the
experiment stays open and fixing the instrumentation becomes the work.
