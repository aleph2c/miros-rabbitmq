import os
import sys
import uuid
import time
import random
from miros.hsm import pp
from pathlib import Path
from dotenv import load_dotenv
from miros.hsm import HsmWithQueues, spy_on
from miros.event import signals, Event, return_status
from miros_rabbitmq.network import NetworkedFactory

env_path = Path('.') / '.env'
if env_path.is_file():
  load_dotenv(env_path)
else:
  # recurse outward to find .env file
  load_dotenv()

RABBIT_USER = os.getenv('RABBIT_USER')
RABBIT_PORT = os.getenv('RABBIT_PORT')
RABBIT_PASSWORD = os.getenv('RABBIT_PASSWORD')
MESH_ENCRYPTION_KEY = os.getenv('MESH_ENCRYPTION_KEY')
SNOOP_SPY_ENCRYPTION_KEY = os.getenv('SNOOP_SPY_ENCRYPTION_KEY')
SNOOP_TRACE_ENCRYPTION_KEY = os.getenv('SNOOP_TRACE_ENCRYPTION_KEY')

'''
  +------------empathy----------------+  Legend:
  |                                   |  a: Other_Advance_War_Cry
  |                         +-dead-+  |  b: Other_Skirmish_War_Cry
  |   +---not_waiting---+   |      |  |  c: Other_Retreat_Ready_War_Cry
  |   |                 |   |      |  |  d: Advance_War_Cry
  |   |   +-waiting-+   |   |      |  |  e: Retreat_War_Cry
  |   |   |         |   +-d->      |  |  f: Other_Retreat_Ready_War_Cry
  |   |   |         |   |   |      |  |  g: Other_Ready_War_Cry
  |   |   |         |   +-e->      |  |  N: Number of other horse archers
  +-a->   |         |   |   |      |  |     detected in the mesh network
  |   |   |         +-d->   |      |  |
  +-b->   |         |   |   |      |  |
  |   |   |         |   |   |      |  |
  +-c->   |         +-e->   |      |  |
  |   |   |         |   |   +------+  |
  |   |   +---------+   |             |
  |   |                 <------f------+
  | *->                 |             |
  |   |                 <------g------+
  |   |                 |             |
  |   +-----------------+             |
  +-----------------------------------+

[ Chart: empathy ] (N per horse archer)
  top     not_waiting                        waiting                       dead
   +-start_at->|                                |                            |
   |           |                                |                            |
   |           +-Other_Retreat_Ready_War_Cry()->|                            |
   |           |              (c)               |                            |
   |           |                                +<----Retreat_War_Cry()------|
   |           |                                |            (e)             |
   |           +-------Advance_War_Cry()--------+--------------------------->|
   |           |              (d)               |                            |
   |           +<-------------------------------+--Other_Advance_War_Cry()---|
   |           |                                |            (a)             |
   |           +-Other_Retreat_Ready_War_Cry()->|                            |
   |           |              (f)               |                            |
   |           |                                +<----Advance_War_Cry()------|
   |           |                                |            (d)             |
   |           +-------Advance_War_Cry()--------+--------------------------->|
   |           |              (d)               |                            |
   |           +<-------------------------------+--Other_Advance_War_Cry()---|
   |           |                                |            (a)             |

'''

@spy_on
def empathy(other, e):
  '''
  empathy HSM outer state
  '''
  status = return_status.UNHANDLED
  if(e.signal == signals.INIT_SIGNAL):
    status = other.trans(not_waiting)
  elif(e.signal == signals.Other_Advance_War_Cry or
       e.signal == signals.Other_Skirmish_War_Cry or
       e.signal == signals.Other_Retreat_War_Cry):
    status = other.trans(not_waiting)
  elif(e.signal == signals.Other_Retreat_Ready_War_Cry or
       e.signal == signals.Other_Ready_War_Cry):
    status = other.trans(waiting)
  else:
    status, other.temp.fun = return_status.SUPER, other.top
  return status

@spy_on
def not_waiting(other, e):
  '''
  'empathy' HSM inner state
          empathy state is the state's parent
  '''
  status = return_status.UNHANDLED
  if(e.signal == signals.Retreat_War_Cry):
    status = other.trans(dead)
  elif(e.signal == signals.Advance_War_Cry):
    status = other.trans(dead)
  else:
    status, other.temp.fun = return_status.SUPER, empathy
  return status

@spy_on
def dead(other, e):
  '''
  'empathy' HSM inner state
          empathy state is the state's parent
  '''
  status = return_status.UNHANDLED
  status, other.temp.fun = return_status.SUPER, empathy
  return status

@spy_on
def waiting(other, e):
  '''
  'empathy' HSM inner state
          not_waiting state is the state's parent
  '''
  status = return_status.UNHANDLED
  if(e.signal == signals.Advance_War_Cry):
    status = other.trans(not_waiting)
  elif(e.signal == signals.Retreat_War_Cry):
    status = other.trans(not_waiting)
  else:
    status, other.temp.fun = return_status.SUPER, not_waiting
  return status

class OtherHorseArcher(HsmWithQueues):

  def __init__(self, name='other', time_compression=1.0):
    super().__init__(name)
    self.name = name

  def dead(self):
    result = self.state_name == 'dead'
    return result

  def waiting(self):
    result = self.state_name == 'waiting'
    return result

  def not_waiting(self):
    result = self.state_name == 'not_waiting'
    return result

class HorseArcher(NetworkedFactory):

  MAXIMUM_ARROW_CAPACITY = 60

  def __init__(self, name=None, time_compression=1.0, rabbit_user=None, rabbit_password=None, rabbit_port=None):

    self.name = name
    super().__init__(name=name,
          rabbit_user=rabbit_user,
          rabbit_password=rabbit_password,
          mesh_encryption_key=MESH_ENCRYPTION_KEY,
          tx_routing_key='archer.{}'.format(name),
          rx_routing_key='archer.#',
          snoop_trace_encryption_key=SNOOP_TRACE_ENCRYPTION_KEY,
          snoop_spy_encryption_key=SNOOP_SPY_ENCRYPTION_KEY
          )
    self.arrows = 0
    self.ticks  = 0
    self.time_compression = time_compression
    self.others = {}

  @staticmethod
  def get_a_name():
    '''
    Provide a unique horse archer name
    '''
    archer_root = random.choice([
      'Hulagu', 'Hadan', 'Gantulga', 'Ganbaatar',
      'Narankhuu', 'Ihbarhasvad', 'Nergui',
      'Narantuyaa', 'Altan', 'Gandbold'])
    archer_name = "{}.{}".format(
      archer_root,
      str(uuid.uuid4())[0:5])
    return archer_name

  def yell(self, event):
    '''
    Yell out this event to the connected mesh network
    '''
    self.transmit(event)

  def compress(self, time_in_seconds):
    '''
    Using the time_compression provided as an input to the constructor we
    convert real seconds into compressed seconds
    '''
    return 1.0 * time_in_seconds / self.time_compression

  def to_time(self, time_in_seconds):
    '''convert real time into horse-archer time'''
    return self.compress(time_in_seconds)

  def add_member_if_needed(self, other_archer_name):
    '''
    If we have not seen this horse archer's name before, then we build an
    empathy statechart for him and place it into the not-waiting state. We add
    this empathy statechart into a dict tracking all other horse archers in
    our unit, the key to access his empathy statechart being his name
    '''
    if self.name != other_archer_name and other_archer_name is not None:
      if other_archer_name not in self.others:
        oha = OtherHorseArcher(other_archer_name)
        oha.start_at(not_waiting)
        self.others[other_archer_name] = oha

  def dispatch_to_all_empathy(self, event):
    '''
    If we are issuing an event that provides us with information about the
    others in our unit we call this method to update ALL of the empathy
    statecharts that we are tracking.

    Note:
      Use this for local events only
    '''
    for name, other in self.others.items():
      other.dispatch(event)

  def dispatch_to_empathy(self, event, other_archer_name=None):
    '''
    If we hear an event on the network that provides us with information
    about a specific unit that we are tracking, we update it's empathy
    statechart with this information.

    Note:
      Use this for event from OTHERS in the mesh network
    '''
    if other_archer_name is None:
      other_archer_name = event.payload
    if other_archer_name is not None:
      self.add_member_if_needed(other_archer_name)
      self.others[other_archer_name].dispatch(event)

def battle_entry(archer, e):
  archer.yell(Event(signal=signals.Other_Announce_Arrival_On_Field, payload=archer.name))
  return return_status.HANDLED

def battle_other_arrival_on_field(archer, e):
  other_archer_name = e.payload
  archer.add_member_if_needed(other_archer_name)
  return return_status.HANDLED

def battle_init(archer, e):
  return archer.trans(deceit_in_detail)

# Deceit-In-Detail-Tactic state callbacks
def didt_entry(archer, e):
  archer.arrows = HorseArcher.MAXIMUM_ARROW_CAPACITY
  archer.ticks  = 0
  archer.post_fifo(
    Event(signal=signals.Second),
    times=0,
    period=archer.to_time(1.0),
    deferred=True)
  return return_status.HANDLED

  archer.cancel_events(Event(signal=signals.Second))
  return return_status.HANDLED

def didt_init(archer, e):
  return archer.trans(advance)

def didt_second(archer, e):
  archer.ticks += 1
  return return_status.HANDLED

def didt_senior_advance_war_cry(archer, e):
  archer.post_fifo(Event(signal=signals.Advance_War_Cry))
  return return_status.HANDLED

def didt_senior_skirmish_war_cry(archer, e):
  archer.post_fifo(Event(signal=signals.Skirmish_War_Cry))
  return return_status.HANDLED

def didt_senior_retreat_war_cry(archer, e):
  archer.post_fifo(Event(signal=signals.Retreat_War_Cry))
  return return_status.HANDLED

def didt_advance_war_cry(archer, e):
  archer.dispatch_to_all_empathy(e)
  return archer.trans(advance)

def didt_other_advance_war_cry(archer, e):
  archer.dispatch_to_empathy(e)
  return archer.trans(advance)

def didt_other_retreat_war_cry(archer, e):
  archer.dispatch_to_empathy(e)
  return archer.trans(feigned_retreat)

def didt_skirmish_war_cry(archer, e):
  return archer.trans(skirmish)

def didt_other_skirmish_war_cry(archer, e):
  archer.dispatch_to_empathy(e)
  return archer.trans(skirmish)

def didt_retreat_war_cry(archer, e):
  archer.dispatch_to_all_empathy(e)
  return archer.trans(feigned_retreat)

def didt_other_retreat_ready_war_cry(archer, e):
  archer.dispatch_to_empathy(e)
  return return_status.HANDLED

def didt_other_ready_war_cry(archer, e):
  archer.dispatch_to_empathy(e)
  return return_status.HANDLED

def didt_reset_tactic(archer, e):
  return archer.trans(deceit_in_detail)

# Advance callbacks
def advance_entry(archer, e):
  archer.yell(Event(signal=signals.Other_Advance_War_Cry, payload=archer.name))
  if len(archer.others) >= 1:
    first_name_of_others = next(iter(archer.others))
    print(archer.others[first_name_of_others].trace())
    archer.others[first_name_of_others].clear_trace()
  archer.snoop_scribble("advancing with {} arrows".format(archer.arrows))

  archer.post_fifo(
    Event(signal=signals.Close_Enough_For_Circle),
    times=1,
    period=archer.to_time(3.0),
    deferred=True)
  return return_status.HANDLED

def advance_exit(archer, e):
  archer.cancel_events(Event(signal=signals.Close_Enough_For_Circle))
  return return_status.HANDLED

def advance_senior_advanced_war_cry(archer, e):
  return return_status.HANDLED

def advance_other_advanced_war_cry(archer, e):
  archer.dispatch_to_empathy(e)
  return return_status.HANDLED

def advance_advance_war_cry(archer, e):
  archer.dispatch_to_all_empathy(e)
  return return_status.HANDLED

def advance_close_enough_for_circle(archer, e):
  return archer.trans(circle_and_fire)

# Circle-And-Fire callbacks
def caf_second(archer, e):
  if(archer.ticks % 6 == 0):
    archer.arrows -= random.randint(1, 3)
    archer.arrows = 0 if archer.arrows < 0  else archer.arrows
    archer.scribble('arrows left {}'.format(archer.arrows))
  if archer.arrows < 20:
    archer.post_fifo(
      Event(signal=
        signals.Skirmish_War_Cry))
  archer.ticks += 1
  return return_status.HANDLED

# Skirmish state callbacks
def skirmish_entry(archer, e):
  archer.yell(Event(signal=signals.Other_Skirmish_War_Cry, payload=archer.name))

  # a Knight could charge at him sometime between 40-120 sec
  # once he enters the skirmish state
  archer.post_fifo(
    Event(signal=signals.Officer_Lured),
    times=1,
    period=archer.to_time(random.randint(40, 200)),
    deferred=True)

  if archer.arrows < 10:
    archer.post_fifo(Event(signal=signals.Ammunition_Low))
  return return_status.HANDLED

def skirmish_exit(archer, e):
  archer.cancel_events(Event(signal=signals.Retreat_War_Cry))
  archer.cancel_events(Event(signal=signals.Officer_Lured))
  return return_status.HANDLED

def skirmish_second(archer, e):
  # While skirmishing, he makes directed attacks on his enemy
  # 40 percent chance of making a shot every 3 seconds
  if archer.ticks % 3 == 0:
    if random.randint(1, 10) <= 4:
      archer.arrows = archer.arrows - 1 if archer.arrows >= 1  else 0
      archer.scribble('arrows left {}'.format(archer.arrows))
  if archer.arrows < 10:
    archer.post_fifo(Event(signal=signals.Ammunition_Low))
  archer.ticks += 1
  return return_status.HANDLED

def skirmish_officer_lured(archer, e):
  archer.snoop_scribble("Knight Charging at {}".format(archer.name))
  archer.post_fifo(
    Event(signal=signals.Retreat_War_Cry))
  return return_status.HANDLED

def skirmish_ammunition_low(archer, e):
  archer.post_fifo(Event(signal=signals.Retreat_Ready_War_Cry))
  return return_status.HANDLED

def skirmish_senior_squirmish_war_cry(archer, e):
  return return_status.HANDLED

def skirmish_other_squirmish_war_cry(archer, e):
  archer.dispatch_to_empathy(e)
  return return_status.HANDLED

def skirmish_skirmish_war_cry(archer, e):
  archer.dispatch_to_all_empathy(e)
  return return_status.HANDLED

def skirmish_retreat_ready_war_cry(archer, e):
  ready = True
  for name, other in archer.others.items():
    if other.dead() is not True:
      ready &= other.waiting()
    else:
      archer.snoop_scribble("{} thinks {} is dead".format(archer.name, name))
  if ready:
    # let's make sure the horse archer's isn't a chicken
    delay_time = random.randint(10, 50)
  else:
    delay_time = random.randint(30, 60)
  archer.post_fifo(
    Event(signal=signals.Retreat_War_Cry),
    times=1,
    period=archer.to_time(delay_time),
    deferred=True)
  return archer.trans(waiting_to_lure)

# Waiting-to-Lure callbacks
def wtl_entry(archer, e):
  archer.yell(Event(signal=signals.Other_Retreat_Ready_War_Cry, payload=archer.name))
  archer.snoop_scribble("{} arrows".format(archer.arrows))
  archer.scribble('put away bow')
  archer.scribble('pull scimitar')
  archer.snoop_scribble("acts scared")
  return return_status.HANDLED

def wtl_second(archer, e):
  archer.ticks += 1
  return return_status.HANDLED

def wtl_ammunition_low(archer, e):
  return return_status.HANDLED

def wtl_exit(archer, e):
  archer.scribble('stash scimitar')
  archer.scribble('pull bow')
  archer.scribble('stop acting')
  return return_status.HANDLED

# Feigned-Retreat callbacks
def fr_entry(archer, e):
  archer.yell(Event(signal=signals.Other_Retreat_War_Cry, payload=archer.name))
  archer.scribble('fire on knights')
  archer.scribble('fire on footman')
  if archer.arrows == 0:
    archer.post_fifo(
      Event(signal=signals.Out_Of_Arrows))
  return return_status.HANDLED

def fr_exit(archer, e):
  archer.cancel_events(Event(signal=signals.Out_Of_Arrows))
  archer.scribble("full gallop")
  return return_status.HANDLED

def fr_second(archer, e):
  if archer.ticks % 3 == 0:
    if random.randint(1, 10) <= 8:
      archer.arrows = archer.arrows - 1 if archer.arrows >= 1  else 0
      archer.scribble('arrows left {}')
    if archer.arrows == 0:
      archer.post_fifo(
        Event(signal=signals.Out_Of_Arrows))
  archer.ticks += 1
  return return_status.HANDLED

def fr_retreat_war_cry(archer, e):
  archer.dispatch_to_all_empathy(e)
  return return_status.HANDLED

def fr_other_retreat_war_cry(archer, e):
  archer.dispatch_to_empathy(e)
  return return_status.HANDLED

def fr_out_of_arrows(archer, e):
  return archer.trans(marshal)

# Marshal callbacks
def marshal_entry(archer, e):
  archer.scribble("halt horse")
  archer.scribble("identify next marshal point")
  archer.scribble("field wrap wounds on self and horse")
  archer.scribble("drink water")
  archer.arrows = HorseArcher.MAXIMUM_ARROW_CAPACITY
  archer.post_fifo(
    Event(signal=signals.Ready),
    times=1,
    period=archer.to_time(60),
    deferred=True)
  return return_status.HANDLED

def marshal_ready(archer, e):
  return archer.trans(waiting_to_advance)

# Waiting-to-Advance callbacks
def wta_entry(archer, e):
  archer.yell(Event(signal=signals.Other_Ready_War_Cry, payload=archer.name))
  ready = True
  archer.snoop_scribble("{} is waiting with {} arrows".format(archer.name, archer.arrows))
  time_to_wait = random.randint(130, 300)
  for name, other in archer.others.items():
    if other.dead() is not True:
      ready &= other.waiting()
    else:
      archer.snoop_scribble("{} thinks {} is dead".format(archer.name, name))

  if ready is False:
    archer.snoop_scribble(
      "{} is impatient he will attack in {} seconds".format(archer.name, time_to_wait))
    archer.post_fifo(Event(signal=signals.Advance_War_Cry),
      times=1,
      period=archer.to_time(time_to_wait),
      deferred=True)
  else:
    archer.snoop_scribble("{} thinks unit is ready to attack".format(archer.name))
    archer.post_fifo(
      Event(signal=signals.Advance_War_Cry))

  return return_status.HANDLED

def wta_exit(archer, e):
  archer.cancel_events(Event(signal=signals.Advance_War_Cry))
  return return_status.HANDLED

# Create the archer
archer = HorseArcher(
  name = HorseArcher.get_a_name(),
  rabbit_user=RABBIT_USER,
  rabbit_password=RABBIT_PASSWORD,
  rabbit_port=RABBIT_PORT,

)

# Create the archer states
battle = archer.create(state='battle'). \
  catch(
    signal=signals.ENTRY_SIGNAL,
    handler=battle_entry). \
  catch(
    signal=signals.INIT_SIGNAL,
    handler=battle_init). \
  catch(
    signal=signals.Other_Arrival_On_Field,
    handler=battle_other_arrival_on_field). \
  to_method()

deceit_in_detail = archer.create(state='deceit_in_detail'). \
  catch(
    signal=signals.ENTRY_SIGNAL,
    handler=didt_entry). \
  catch(
    signal=signals.INIT_SIGNAL,
    handler=didt_init). \
  catch(
    signal=signals.Second,
    handler=didt_second). \
  catch(
    signal=signals.Senior_Advance_War_Cry,
    handler=didt_senior_advance_war_cry). \
  catch(
    signal=signals.Senior_Skirmish_War_Cry,
    handler=didt_senior_skirmish_war_cry). \
  catch(
    signal=signals.Senior_Retreat_War_Cry,
    handler=didt_senior_retreat_war_cry). \
  catch(
    signal=signals.Advance_War_Cry,
    handler=didt_advance_war_cry). \
  catch(
    signal=signals.Other_Advance_War_Cry,
    handler=didt_other_advance_war_cry). \
  catch(
    signal=signals.Skirmish_War_Cry,
    handler=didt_skirmish_war_cry). \
  catch(
    signal=signals.Other_Skirmish_War_Cry,
    handler=didt_other_skirmish_war_cry). \
  catch(
    signal=signals.Retreat_War_Cry,
    handler=didt_retreat_war_cry). \
  catch(
    signal=signals.Other_Retreat_War_Cry,
    handler=didt_other_retreat_war_cry). \
  catch(
    signal=signals.Other_Retreat_Ready_War_Cry,
    handler=didt_other_retreat_ready_war_cry). \
  catch(
    signal=signals.Other_Ready_War_Cry,
    handler=didt_other_ready_war_cry). \
  catch(
    signal=signals.Reset_Tactic,
    handler=didt_reset_tactic). \
  to_method()

advance = archer.create(state='advance'). \
  catch(
    signal=signals.ENTRY_SIGNAL,
    handler=advance_entry).  \
  catch(
    signal=signals.EXIT_SIGNAL,
    handler=advance_exit).  \
  catch(
    signal=signals.Senior_Advance_War_Cry,
    handler=advance_senior_advanced_war_cry).  \
  catch(
    signal=signals.Other_Advance_War_Cry,
    handler=advance_other_advanced_war_cry).  \
  catch(
    signal=signals.Advance_War_Cry,
    handler=advance_advance_war_cry).  \
  catch(
    signal=signals.Close_Enough_For_Circle,
    handler=advance_close_enough_for_circle). \
  to_method()

circle_and_fire = archer.create(state='circle_and_fire'). \
  catch(
    signal=signals.Second,
    handler=caf_second). \
  to_method()

skirmish = archer.create(state='skirmish'). \
  catch(
    signal=signals.ENTRY_SIGNAL,
    handler=skirmish_entry). \
  catch(
    signal=signals.EXIT_SIGNAL,
    handler=skirmish_exit). \
  catch(
    signal=signals.Second,
    handler=skirmish_second). \
  catch(
    signal=signals.Officer_Lured,
    handler=skirmish_officer_lured). \
  catch(
    signal=signals.Ammunition_Low,
    handler=skirmish_ammunition_low). \
  catch(
    signal=signals.Senior_Skirmish_War_Cry,
    handler=skirmish_senior_squirmish_war_cry). \
  catch(
    signal=signals.Other_Skirmish_War_Cry,
    handler=skirmish_other_squirmish_war_cry). \
  catch(
    signal=signals.Skirmish_War_Cry,
    handler=skirmish_skirmish_war_cry). \
  catch(
    signal=signals.Retreat_Ready_War_Cry,
    handler=skirmish_retreat_ready_war_cry). \
  to_method()

waiting_to_lure = archer.create(state='waiting_to_lure'). \
  catch(
    signal=signals.ENTRY_SIGNAL,
    handler=wtl_entry). \
  catch(
    signal=signals.EXIT_SIGNAL,
    handler=wtl_exit). \
  catch(
    signal=signals.Second,
    handler=wtl_second). \
  catch(
    signal=signals.Ammunition_Low,
    handler=wtl_ammunition_low). \
  to_method()

feigned_retreat = archer.create(state='feigned_retreat'). \
  catch(
    signal=signals.ENTRY_SIGNAL,
    handler=fr_entry). \
  catch(
    signal=signals.EXIT_SIGNAL,
    handler=fr_exit). \
  catch(
    signal=signals.Second,
    handler=fr_second). \
  catch(
    signal=signals.Out_Of_Arrows,
    handler=fr_out_of_arrows). \
  catch(
    signal=signals.Retreat_War_Cry,
    handler=fr_retreat_war_cry). \
  catch(
    signal=signals.Other_Retreat_War_Cry,
    handler=fr_other_retreat_war_cry). \
  to_method()

marshal = archer.create(state='marshal'). \
  catch(
    signal=signals.ENTRY_SIGNAL,
    handler=marshal_entry). \
  catch(
    signal=signals.Ready,
    handler=marshal_ready). \
  to_method()

waiting_to_advance = archer.create(state='waiting_to_advance'). \
  catch(
    signal=signals.ENTRY_SIGNAL,
    handler=wta_entry). \
  catch(
    signal=signals.EXIT_SIGNAL,
    handler=wta_exit). \
  to_method()

archer.nest(battle, parent=None). \
  nest(deceit_in_detail, parent=battle). \
  nest(advance, parent=deceit_in_detail). \
  nest(circle_and_fire, parent=advance). \
  nest(skirmish, parent=deceit_in_detail). \
  nest(waiting_to_lure, parent=skirmish). \
  nest(feigned_retreat, parent=deceit_in_detail). \
  nest(marshal, parent=deceit_in_detail). \
  nest(waiting_to_advance, parent=marshal)

if __name__ == '__main__':
  random.seed()
  print("I am {}".format(archer.name))
  archer.time_compression = 10
  snoop_type = sys.argv[1:]
  if len(snoop_type) >= 1:
    if snoop_type[0] == 'trace':
      archer.enable_snoop_trace()
    elif snoop_type[0] == 'spy':
      archer.enable_snoop_spy()
  else:
    archer.live_trace = True
  archer.start_at(battle)

  archer.post_fifo(Event(signal=signals.Senior_Advance_War_Cry))
  time.sleep(1800)


