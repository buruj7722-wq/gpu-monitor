from monitor.alerts import AlertEngine
from monitor.config import AlertConfig
from monitor.models import CPU, GPU, GPUReading, Snapshot, Source, SystemReading


def sample(t, cpu=0, temp=40, max_temp=None):
    return Snapshot(
        timestamp=t,
        system=SystemReading(cpu=CPU(usage_percent=cpu)),
        gpu=GPUReading(
            source=Source(status="ok"),
            devices=[GPU(index=0, uuid="GPU-a", temperature_c=temp, temperature_max_c=max_temp)],
        ),
    )


def test_sustain_hysteresis_recovery_and_no_repeated_since():
    engine = AlertEngine(AlertConfig())
    assert not engine.evaluate(sample(0, 95), 0)
    assert not engine.evaluate(sample(29, 95), 29)
    active = engine.evaluate(sample(30, 95), 30)
    assert active[0].id == "cpu/high"
    assert engine.evaluate(sample(31, 88), 31)[0].since == 30
    assert engine.evaluate(sample(32, 80), 32)
    assert not engine.evaluate(sample(42, 80), 42)


def test_missing_value_does_not_clear_active():
    engine = AlertEngine(AlertConfig(sustain_seconds=0))
    assert engine.evaluate(sample(0, 99), 0)[0].severity == "critical"
    assert engine.evaluate(sample(1, None), 1)[0].value is None


def test_no_invented_thermal_limit():
    engine = AlertEngine(AlertConfig(sustain_seconds=0))
    assert not any(a.id.endswith("temperature") for a in engine.evaluate(sample(0, temp=85), 0))
    alerts = engine.evaluate(sample(1, temp=86, max_temp=90), 1)
    assert any(a.id.endswith("temperature") and a.severity == "warning" for a in alerts)


def test_gpu_outage_duration():
    engine = AlertEngine(AlertConfig())
    assert not engine.evaluate(Snapshot(timestamp=0), 0)
    assert not engine.evaluate(Snapshot(timestamp=9), 9)
    assert engine.evaluate(Snapshot(timestamp=10), 10)[0].id == "gpu/unavailable"
