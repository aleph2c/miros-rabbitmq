
import time
import uuid
import random
from miros import spy_on
from miros import signals, Event, return_status
from miros_rabbitmq import NetworkedActiveObject

def make_name(post):
  return str(uuid.uuid4())[0:5] + '_' + post

def outer_init(chart, e):
  chart.post_fifo(
    Event(signal=signals.to_inner),
    times=1,
    period=random.randint(2, 7),
    deferred=True)
  chart.transmit(Event(signal=signals.other_to_outer, payload=chart.name))
  return return_status.HANDLED

def outer_to_inner(chart, e):
  return chart.trans(inner)

def outer_other_to_inner(chart, e):
  return chart.trans(inner)

def inner_entry(chart, e):
  chart.post_fifo(
    Event(signal=signals.to_outer),
    times=1,
    period=random.randint(2, 7),
    deferred=True)
  chart.transmit(Event(signal=signals.other_to_inner, payload=chart.name))
  chart.snoop_scribble(chart.this_url())

  return return_status.HANDLED

def inner_exit(chart, e):
  chart.cancel_events(Event(signal=signals.to_outer))
  return return_status.HANDLED

def inner_other_to_inner(chart, e):
  return return_status.HANDLED

def inner_to_inner(chart, e):
  return return_status.HANDLED

def inner_to_outer(chart, e):
  return chart.trans(outer)

def inner_other_to_outer(chart, e):
  return chart.trans(outer)

@spy_on
def inner(chart, e):
  status = return_status.UNHANDLED
  if(e.signal == signals.ENTRY_SIGNAL):
    status = inner_entry(chart, e)
  elif(e.signal == signals.INIT_SIGNAL):
    status = return_status.HANDLED
  elif(e.signal == signals.to_outer):
    status = inner_to_outer(chart, e)
  elif(e.signal == signals.other_to_outer):
    status = inner_other_to_outer(chart, e)
  elif(e.signal == signals.other_to_inner):
    status = inner_other_to_inner(chart, e)
  elif(e.signal == signals.to_inner):
    status = inner_to_inner(chart, e)
  elif(e.signal == signals.EXIT_SIGNAL):
    status = inner_exit(chart, e)
  else:
    status, chart.temp.fun = return_status.SUPER, outer
  return status

@spy_on
def outer(chart, e):
  status = return_status.UNHANDLED
  if(e.signal == signals.ENTRY_SIGNAL):
    status = return_status.HANDLED
  elif(e.signal == signals.INIT_SIGNAL):
    status = outer_init(chart, e)
  elif(e.signal == signals.to_inner):
    status = outer_to_inner(chart, e)
  elif(e.signal == signals.other_to_inner):
    status = outer_other_to_inner(chart, e)
  elif(e.signal == signals.EXIT_SIGNAL):
    status = return_status.HANDLED
  else:
    status, chart.temp.fun = return_status.SUPER, chart.top
  return status


if __name__ == '__main__':
  random.seed()
  ao = NetworkedActiveObject(make_name('ao'),
                              rabbit_user='bob',
                              rabbit_password='dobbs',
                              tx_routing_key='heya.man',
                              rx_routing_key='#.man',
                              mesh_encryption_key=b'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg=')
  # To log
  #ao.enable_snoop_spy()
  #ao.enable_snoop_spy_no_color()
  ao.enable_snoop_trace()
  #ao.enable_snoop_trace_no_color()
  # python3 networkable_active_object.py 2>&1 | sed -r 's/'$(echo -e "\033")'\[[0-9]{1,2}(;([0-9]{1,2})?)?[mK]//g' | tee log.txt
  # grep -F [+s] log.txt | grep <name>
  ao.start_at(outer)
  time.sleep(20)


