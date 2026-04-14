from app import db


class HighPriorityRanking(db.Model):
    """Persists card ordering within the HIGH priority column per status tab."""

    __tablename__ = "high_priority_rankings"

    id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    coid   = db.Column(db.String, nullable=False)   # Card ID e.g. "CO-001", "CO-001-P"
    status = db.Column(db.String, nullable=False)    # "inprocess" / "packed"
    rank   = db.Column(db.Integer, nullable=False)   # 0-based position

    __table_args__ = (
        db.UniqueConstraint('coid', 'status', name='uq_high_card_status'),
    )

    def __repr__(self):
        return f"<HighPriorityRanking {self.coid} rank={self.rank}>"


class MediumPriorityRanking(db.Model):
    """Persists card ordering within the MEDIUM priority column per status tab."""

    __tablename__ = "medium_priority_rankings"

    id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    coid   = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    rank   = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('coid', 'status', name='uq_medium_card_status'),
    )

    def __repr__(self):
        return f"<MediumPriorityRanking {self.coid} rank={self.rank}>"


class LowPriorityRanking(db.Model):
    """Persists card ordering within the LOW priority column per status tab."""

    __tablename__ = "low_priority_rankings"

    id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    coid   = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    rank   = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('coid', 'status', name='uq_low_card_status'),
    )

    def __repr__(self):
        return f"<LowPriorityRanking {self.coid} rank={self.rank}>"


# Helper to get the right model by priority name
RANKING_MODELS = {
    "High":   HighPriorityRanking,
    "Medium": MediumPriorityRanking,
    "Low":    LowPriorityRanking,
}
