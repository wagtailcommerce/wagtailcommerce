from django.dispatch import Signal

order_paid_signal = Signal(providing_args=['order'])

order_shipment_generation_failure_signal = Signal(providing_args=['order'])
order_shipment_generated_signal = Signal(providing_args=['order'])
