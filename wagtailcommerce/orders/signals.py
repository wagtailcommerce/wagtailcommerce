from django.dispatch import Signal

order_paid = Signal(providing_args=['order'])

shipment_generated = Signal(providing_args=['order'])
