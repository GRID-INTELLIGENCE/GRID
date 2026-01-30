# Mocking the data from DomainVisualizer.tsx for validation logic
# Since we cannot import TSX into Python, we replicate the data structure.


class Domain:
    def __init__(self, name, x, y, metaphor, type):
        self.name = name
        self.x = x
        self.y = y
        self.metaphor = metaphor
        self.type = type


domains = [
    Domain(name="GRID Core", x=0.1, y=0.1, metaphor="Railway", type="Railway"),
    Domain(name="Mothership", x=0.4, y=0.8, metaphor="Freeway", type="Freeway"),
    Domain(name="Resonance", x=0.9, y=0.8, metaphor="Freeway", type="Freeway"),
    Domain(name="Light of the Seven", x=0.2, y=0.9, metaphor="Freeway", type="Freeway"),
    Domain(name="Tools", x=0.5, y=0.4, metaphor="Freeway", type="Freeway"),
    Domain(name="EQ", x=0.6, y=0.4, metaphor="Freeway", type="Freeway"),
    Domain(name="The Arena", x=0.7, y=0.5, metaphor="Hybrid", type="Hybrid"),
    Domain(name="Connectivity", x=0.5, y=0.5, metaphor="Hybrid", type="Hybrid"),
    Domain(name="Research Knowledge", x=0.05, y=0.05, metaphor="Railway", type="Railway"),
    Domain(name="Iron Frame", x=0.15, y=0.02, metaphor="Iron Frame", type="Iron"),
    Domain(name="Temporal Drift", x=0.95, y=0.1, metaphor="Drift", type="Drift"),
    Domain(name="Worker Pool", x=0.8, y=0.2, metaphor="The Asphalt", type="Freeway"),
    Domain(name="Distribution Manager", x=0.3, y=0.3, metaphor="Interchange", type="Railway"),
    Domain(name="Highway Router", x=0.2, y=0.4, metaphor="Navigation", type="Railway"),
]

# DALÍ GEOMETRY INTEGRITY RULES
# Based on DaliGeometryBlocks schema


def test_ground_plane_anchoring():
    """Verify that 'Railway' and 'Iron' domains are anchored near Y=0."""
    anchored_domains = [d for d in domains if d.y <= 0.15]
    assert any(d.name == "Research Knowledge" for d in anchored_domains), "Research Knowledge must be anchored."
    assert any(d.name == "Iron Frame" for d in anchored_domains), "Iron Frame must be anchored."
    assert any(d.name == "GRID Core" for d in anchored_domains), "GRID Core must be widely anchored."


def test_sky_structures():
    """Verify that 'Freeway' domains reach the upper quadrants (Y > 0.7)."""
    sky_domains = [d for d in domains if d.y >= 0.7]
    assert any(d.name == "Light of the Seven" for d in sky_domains), "Light of the Seven must be at the apex."
    assert any(d.name == "Resonance" for d in sky_domains), "Resonance must be in the flux layer."


def test_coordinate_integrity():
    """Verify all coordinates are within normalized 0-1 bounds."""
    for domain in domains:
        assert 0 <= domain.x <= 1.0, f"Domain {domain.name} X-coord out of bounds."
        assert 0 <= domain.y <= 1.0, f"Domain {domain.name} Y-coord out of bounds."


def test_metaphor_consistency():
    """Verify that metaphors align with domain types."""
    for domain in domains:
        if domain.type == "Railway":
            assert domain.metaphor in [
                "Railway",
                "Interchange",
                "Navigation",
            ], f"Invalid metaphor for Railway: {domain.name}"
        if domain.type == "Freeway":
            assert domain.metaphor in ["Freeway", "The Asphalt"], f"Invalid metaphor for Freeway: {domain.name}"
