import pandas as pd
from pyknow import *
import random

all_pokemon = pd.read_csv('Pokemon.csv')
regular_pokemon = all_pokemon[all_pokemon['Legendary']==False]

"""#Expert System"""

#For reference - pokemon_card dict (According to card number)
'''
    col0 = Pokemon Name
    col1 = Type
    col2 = Attack
    col3 = Defense
'''

#For reference - Comparison of types
''' Water beats Fire
    Electric beats Water
    Grass beats Rock
    Rock beats Electric
    Fire beats Grass'''

# The Fact Subclases

class PokemonES(Fact):
    """
    Holds game Facts (moving from rule to rule)
    """
    pass

class RegularPokemonCards(Fact):
    """
    Info about the regular cards in the deck
    """
    p_key = Field(int, mandatory=True)
    p_name = Field(str, mandatory=True)
    p_type = Field(str, mandatory=True)
    p_attack = Field(int, mandatory=True)
    p_defense = Field(int, mandatory=True)

class AllPokemonCards(Fact):
    """
    Info about the cards in the full deck
    """
    p_key = Field(int, mandatory=True)
    p_name = Field(str, mandatory=True)
    p_type = Field(str, mandatory=True)
    p_attack = Field(int, mandatory=True)
    p_defense = Field(int, mandatory=True)

class ComputerAttackDifficulty(Fact):
    """
    Will store the user's selection for the computer's difficulty.
    We have two options:
    EASIER - when attacking, the computer will select a card at random
    HARDER - the computer will always use its card with the strongest attack

    NOTE: the computer's defense choices will be determined by the Expert System
    """
    diff = Field(int, mandatory=True)

class UserCards(Fact):
    """
    Holds the user's cards for this round
    """
    pass

class ComputerCards(Fact):
    """
    Holds the computer's cards for this round
    """
    pass

class HP(Fact):
    """
    User and computer's overall health
    This will be updated each round
    """
    user = Field(int, mandatory=True)
    computer = Field(int, mandatory=True)

class LegendaryThreshold(Fact):
    """
    This will hold the threshold that, when hit, will trigger the legendary deck.
    It will be 25% of whatever is set as the starting HP.
    """
    pass

class LegendaryRounds(Fact):
    """
    Keeps track of when the legendary rounds are reached.
    The first time, a message will be displayed and the user will be given an 
    advantage if they are behind.  After that, the normal game will continue, 
    only with the additional cards.
    """
    leg_rounds = Field(int, mandatory=True)

class RoundNumber(Fact):
    """
    The round number will determine who goes first on any given draw
    Will be updated each round
    """
    round_num = Field(int, mandatory=True)
    
class UserCard(Fact):
    """
    The user's choice for the round
    This will hold the index of the card 
    From here, we can access the knowledge base to extract the type, attack, defense when needed
    """
    pass

class UserCardType(Fact):
    """
    This will hold the user's card type.  This will be the basis upon which the computer
    chooses its card to play.
    """
    pass

class ComputerCard(Fact):
    """
    The computer's choice for the round
    """
    pass

class ComputerCardTypes(Fact):
    """
    This will store the types of the computer's five cards during each round
    """
    pass

class ComputerCardType(Fact):
    """
    This will store the type of the computer's chosen card each round
    """
    pass

class WhoGetsMultiplier(Fact):
    """
    This will store who is awarded the multiplier after the type comparison
    It will change round to round based on the type comparisons
    """
    pass

class Multiplier(Fact):
    """
    This will store what the multiplier is for the given round
    It will change based on the type comparisons 
    """
    pass 



# The Knowledge Engine
class PlayPokemonES(KnowledgeEngine):
    # DefFacts is called every time the reset method is
    # This includes generators of the facts needed by the game
    # We store here all of the available Pokemon cards and their attributes
    @DefFacts()
    def game_settings(self):
        # Dictionary of avaiable regular Pokemon 
        self.pokemon_cards = dict()
        for i in range(len(regular_pokemon)):
            yield RegularPokemonCards(p_key = int(regular_pokemon['#'][i]), p_name=regular_pokemon['Name'][i], 
                               p_type=regular_pokemon['Type 1'][i], p_attack=int(regular_pokemon['Attack'][i]), 
                               p_defense=int(regular_pokemon['Defense'][i]))
        
        # Dictionary of avaiable Pokemon (with Legendary added) 
        self.all_pokemon_cards = dict()
        for i in range(len(all_pokemon)):
            yield AllPokemonCards(p_key = int(all_pokemon['#'][i]), p_name=all_pokemon['Name'][i], 
                               p_type=all_pokemon['Type 1'][i], p_attack=int(all_pokemon['Attack'][i]), 
                               p_defense=int(all_pokemon['Defense'][i]))        
    
    # Store the dictionary of the regular pokemon cards
    @Rule(NOT(PokemonES()), RegularPokemonCards(p_key=MATCH.p_key, p_name=MATCH.name, p_type=MATCH.p_type, 
                                         p_attack=MATCH.attack, p_defense=MATCH.defense))
    def def_pokemon_cards(self, p_key, name, p_type, attack, defense):
          self.pokemon_cards[p_key] = [name, p_type, attack, defense]
    
    # Store the dictionary of the full deck of pokemon cards
    @Rule(NOT(PokemonES()), AllPokemonCards(p_key=MATCH.p_key, p_name=MATCH.name, p_type=MATCH.p_type, 
                                         p_attack=MATCH.attack, p_defense=MATCH.defense))
    def def_all_pokemon_cards(self, p_key, name, p_type, attack, defense):
          self.all_pokemon_cards[p_key] = [name, p_type, attack, defense]
    
    # Define what happens when the game is started
    @Rule()
    def new_game(self):
        print('Let\'s play PokemonBattlES!')
        start_HP = int(input('Enter Starting HP (min 200): '))
        # Set the starting values for user and computer's HP
        self.declare(HP(user=start_HP, computer=start_HP))
        # Set the value that will trigger the legendary deck
        self.declare(LegendaryThreshold(int(start_HP*0.25)))
        # Set the computer's attack difficulty level
        c_diff = int(input('Choose Computer\'s Attack Strategy (0 for random, 1 for optimal): '))
        # Store this fact
        self.declare(ComputerAttackDifficulty(diff=c_diff))
        # Reset to start at round one
        self.declare(RoundNumber(round_num=1))
        # Set the legendary round counter to 0 
        self.declare(LegendaryRounds(leg_rounds=0))
        # Move to next rule
        self.declare(PokemonES('show_scores'))
    
    # This is where we will begin each round as the game progresses 
    # Showing scores and round number
    @Rule(AS.f1 << PokemonES('show_scores'), 
          AS.f2 << HP(user=MATCH.uhp,
            computer=MATCH.chp), 
          AS.f3 << RoundNumber(round_num=MATCH.rnum),
          AS.f4 << LegendaryThreshold(MATCH.legthresh))
    def print_current_scores(self, f1, f2, f3, uhp, chp, rnum, legthresh):
        self.retract(f1)
        # NOTE: we do not retract HP and Round Number because these are being maintained 
        # throughout the game
        print('Round:', rnum)
        print('\nCurrent HP: ')
        print('You:', uhp)
        print('Computer:', chp)

        # We want to check if the threshold to change the deck has been hit 
        if uhp <= legthresh or chp <= legthresh:
          self.declare(PokemonES('threshold_hit'))
        else:
          self.declare(PokemonES('deal'))

    # If the legendary threshold is hit we introduce the legendary Pokemon into the deck
    @Rule(AS.f1 << PokemonES('threshold_hit'),
          AS.f2 << LegendaryRounds(leg_rounds=MATCH.lrounds),
          AS.f3 << HP(user=MATCH.uhp,
            computer=MATCH.chp))
    def thresh_hit(self, f1, f2, f3, lrounds, uhp, chp):
        self.retract(f1)
        # The first time it is hit, a message will be displayed
        if lrounds == 0:
          print('\nTHE END GAME HAS BEEN REACHED')
          print('Legendary Pokemon have been added to the deck.')
          print('Legendary Pokemon receive a 1.5 multiplier against all regular Pokemon.')
          # Update the legendary rounds fact so this bonus isn't given again
          self.modify(f2, leg_rounds=lrounds+1)
          # If the user is trailing at this point, they will be guaranteed to receive
          # a legendary Pokemon in the next round
          if uhp < chp:
            print('\nYou are behind! Here is a bonus to help you catch up.')
            self.declare(PokemonES('user_behind_legendary'))
          else:
            # Otherwise, both players will continue and the full deck will be used
            print('\nYou are ahead! Keep going!')
            self.declare(PokemonES('deal_full_deck'))
        else:
          # Following the first end game round, it will continue to use the full deck
          self.declare(PokemonES('deal_full_deck'))
    
    # If the user is behind the first time the threshold is hit, they will be guaranteed
    # to receive a legendary Pokemon in the next round.
    @Rule(AS.f1 << PokemonES('user_behind_legendary'))
    def user_behind_legendary(self, f1):
        self.retract(f1)
        print('\nDealing..............')
        # Get the list of all Pokemon cards
        card_nums = list(self.all_pokemon_cards.keys())
        # Get the list of Legendary Pokemon cards
        leg_nums = []
        for card in card_nums:
          if self.all_pokemon_cards[card][1] == 'Legendary':
            leg_nums.append(card)
        # Give one of these randomly to the user
        u_bonus = random.choice(leg_nums)
        # Take this card out of the deck
        card_nums.remove(u_bonus)

        # Now, cards will be dealt randomly from the entire deck until each has five 
        # Select 9 random cards
        dealt_cards = random.sample(card_nums, 9)

        # We will alternate dealing - starting with the computer
        user_cards = []
        computer_cards = []

        # Add the user's legendary card to their hand
        user_cards.append(u_bonus)
        # Deal with the rest
        i = 0
        # Give one to the computer to even the hands
        computer_cards.append(dealt_cards[-1])
        while i < (len(dealt_cards)-2):
          user_cards.append(dealt_cards[i])
          computer_cards.append(dealt_cards[i+1])
          i += 2
        # Store the user and computer's cards for this round
        self.declare(UserCards(user_cards))
        self.declare(ComputerCards(computer_cards))
        # Move to show the user their cards
        self.declare(PokemonES('show_user_cards'))
    
    # Deal regular cards to user and computer
    @Rule(AS.f1 << PokemonES('deal'))
    def deal_cards(self, f1):
        self.retract(f1)
        print('\nDealing..............')
        # Get the list of all available cards
        card_nums = list(self.pokemon_cards.keys())
        # Select 10 random cards
        dealt_cards = random.sample(card_nums, 10)
        
        # Here we will deal these cards - alternating back and forth between players
        user_cards = []
        computer_cards = []
        
        i = 0
        while i < (len(dealt_cards)):
            user_cards.append(dealt_cards[i])
            computer_cards.append(dealt_cards[i+1])
            i += 2
        # Store the user and computer's cards for this round
        self.declare(UserCards(user_cards))
        self.declare(ComputerCards(computer_cards))
        self.declare(PokemonES('show_user_cards'))

    # Deal the full deck of cards to user and computer
    @Rule(AS.f1 << PokemonES('deal_full_deck'))
    def deal_full_deck(self, f1):
        self.retract(f1)
        print('\nDealing..............')
        # Get the list of all available cards
        card_nums = list(self.all_pokemon_cards.keys())
        # Select 10 random cards
        dealt_cards = random.sample(card_nums, 10)
        
        # Here we will deal these cards - alternating back and forth between players
        user_cards = []
        computer_cards = []
        
        i = 0
        while i < (len(dealt_cards)):
            user_cards.append(dealt_cards[i])
            computer_cards.append(dealt_cards[i+1])
            i += 2
        # Store the user and computer's cards for this round
        self.declare(UserCards(user_cards))
        self.declare(ComputerCards(computer_cards))
        self.declare(PokemonES('show_user_cards'))

    # Show the user their cards
    @Rule(AS.f1 << PokemonES('show_user_cards'), UserCards(MATCH.u_cards))
    def show_user_cards(self, f1, u_cards):
        self.retract(f1)
        print('\nHere are your cards!')
        print('.....................')
        # Print the user their available cards, along with the attributes of each
        for i in u_cards:
            print(i, self.all_pokemon_cards[i][0])
            print('Type: {}, Attack: {}, Defense: {}'.format(self.all_pokemon_cards[i][1], 
                                                             self.all_pokemon_cards[i][2], 
                                                             self.all_pokemon_cards[i][3]))
            print('.....................')
        self.declare(PokemonES('whose_turn'))
    
    # Determine whose turn it is
    @Rule(AS.f1 << PokemonES('whose_turn'), RoundNumber(round_num=MATCH.rnum))
    def whose_turn(self, f1, rnum):
        self.retract(f1)
        # We will have the player go first on odd numbered rounds, and the computer
        # on even numbered rounds
        if rnum%2 != 0:
            self.declare(PokemonES('user_plays_first'))
        else:
            self.declare(PokemonES('computer_plays_first'))
    
    ####
    #
    # CASE 1:  the player goes first (odd numbered rounds)
    #
    ####
    # When the player goes first, they are free to play any card they wish
    @Rule(AS.f1 << PokemonES('user_plays_first'), 
          AS.f2 << UserCards(MATCH.u_cards))
    def user_plays_first(self, f1, f2, u_cards):
        self.retract(f1)
        # We are finished with the user's set of cards for this round
        self.retract(f2)
        print('\nIt\'s your turn.')
        print('You are on the ATTACK!') 
        print('\nSelect a card to play.')
        # We get the user's selection
        # We handle if they enter a value corresponding to a card they do not have 
        while True:
            choice = int(input('Enter card number: '))
            if choice in list(u_cards):
                break
            else:
                print('You don\'t have that card!')
        print('\nYou play {}!'.format(self.all_pokemon_cards[choice][0]))
        # Store the user's selection and move to computer
        self.declare(UserCard(choice))
        # Store the type of the user's card choice
        self.declare(UserCardType(self.all_pokemon_cards[choice][1]))
        self.declare(PokemonES('computer_plays_second'))
        
    ####
    # COMPUTER PLAYS SECOND
    ####

    # The computer will make its decision based on the type of the user's card
    @Rule(AS.f1 << PokemonES('computer_plays_second'),
          AS.f2 << UserCardType(MATCH.u_type),
          AS.f3 << ComputerCards(MATCH.c_cards))
    def computer_plays_second(self, f1, f2, f3, u_type, c_cards):
        self.retract(f1)
        # First, we want to store the computer's card types
        c_types = [] 
        for card in c_cards:
          c_types.append(self.all_pokemon_cards[card][1])
        
        # We will store this as a fact
        self.declare(ComputerCardTypes(c_types))
        # Then the computer will base its action on the its best matchup 
        # NOTE:  It will always take into account the multiplier (based on types)
        # and then also see if it has a better option. 
        if u_type == 'Fire':
            self.declare(PokemonES('comp_vs_fire'))
        elif u_type == 'Water':
            self.declare(PokemonES('comp_vs_water'))
        elif u_type == 'Grass':
            self.declare(PokemonES('comp_vs_grass'))
        elif u_type == 'Electric':
            self.declare(PokemonES('comp_vs_electric'))
        elif u_type == 'Rock':
            self.declare(PokemonES('comp_vs_rock'))
        elif u_type == 'Legendary':
            self.declare(PokemonES('comp_vs_legendary'))
      
    @Rule(AS.f1 << PokemonES('comp_vs_fire'),
          AS.f2 << ComputerCardTypes(MATCH.c_types),
          AS.f3 << ComputerCards(MATCH.c_cards))
    def comp_vs_fire(self, f1, f2, f3, c_types, c_cards):
        # Here, water will give a bonus
        # We will see if the computer has a water Pokemon, calculate the bonus 
        # And then see if it can do better with its other cards.
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        # Get the indexes of all the computer's water Pokemon
        water = [i for i,x in enumerate(c_types) if x == 'Water']
        # For each of these, get corresponding Pokemon
        water_pokemon = []
        for i in water:
          water_pokemon.append(c_cards[i])
        # For each of these, get the defense statistics
        water_defenses = []
        for i in water_pokemon:
          water_defenses.append(self.all_pokemon_cards[i][3])

        # If the computer has water Pokemon, get the max defense
        if water_defenses:
          # Get the highest of these water defense values
          max_water_def = max(water_defenses)
          # Get the index of this within this list
          max_water_def_index = water_defenses.index(max_water_def)
          # Get the actual Pokemon card # of this best water defense
          best_water = water_pokemon[max_water_def_index]
        else:
          # The computer has no water Pokemon
          max_water_def = 0
        # We now want to check if the computer has a better option
        # Since water beats fire, this will be awarded the 1.2 multiplier
        max_water_def = int(max_water_def * 1.2)

        # Get the computer's non-water Pokemon
        comp_others = []
        for i in c_cards:
          if i not in water_pokemon:
            comp_others.append(i)
        # Get the defense statistics for these
        # Remember, the a legendary will get a 1.5 times boost vs all regular cards
        other_defs = []
        for i in comp_others:
          if self.all_pokemon_cards[i][1] == 'Legendary':
            other_defs.append(int(self.all_pokemon_cards[i][3]*1.5))
          else:
            other_defs.append(self.all_pokemon_cards[i][3])
        # Get the highest value
        if other_defs:
          other_defs_max = max(other_defs)
        else:
          other_defs_max = 0
        # Now, make the comparison
        if max_water_def >= other_defs_max:
          # The computer will play its best water Pokemon
          # Store the card number
          self.declare(ComputerCard(best_water))
          # Move to the compare types stage
          self.declare(PokemonES('comp_play'))
        else:
          # The computer has a better play than its best water
          # Get index of its best defense
          best_other_ind = other_defs.index(other_defs_max)
          # Get the Pokemon card number
          best_other = comp_others[best_other_ind]
          # Store the card number
          self.declare(ComputerCard(best_other))
          # Move to the compare types stage
          self.declare(PokemonES('comp_play'))
    
    @Rule(AS.f1 << PokemonES('comp_vs_water'),
          AS.f2 << ComputerCardTypes(MATCH.c_types),
          AS.f3 << ComputerCards(MATCH.c_cards))
    def comp_vs_water(self, f1, f2, f3, c_types, c_cards):
        # Here, electric will give a bonus
        # We will see if the computer has an electric Pokemon, calculate the bonus 
        # And then see if it can do better with its other cards.
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        # Get the indexes of all the computer's electric Pokemon
        electric = [i for i,x in enumerate(c_types) if x == 'Electric']
        # For each of these, get corresponding Pokemon
        electric_pokemon = []
        for i in electric:
          electric_pokemon.append(c_cards[i])
        # For each of these, get the defense statistics
        electric_defenses = []
        for i in electric_pokemon:
          electric_defenses.append(self.all_pokemon_cards[i][3])

        # If the computer has electric Pokemon, get the max defense
        if electric_defenses:
          # Get the highest of these electric defense values
          max_electric_def = max(electric_defenses)
          # Get the index of this within this list
          max_electric_def_index = electric_defenses.index(max_electric_def)
          # Get the actual Pokemon card # of this best electric defense
          best_electric = electric_pokemon[max_electric_def_index]
        else:
          # The computer has no electric Pokemon
          max_electric_def = 0
        # We now want to check if the computer has a better option
        # Since electric beats water, this will be awarded the 1.2 multiplier
        max_electric_def = int(max_electric_def * 1.2)

        # Get the computer's non-electric Pokemon
        comp_others = []
        for i in c_cards:
          if i not in electric_pokemon:
            comp_others.append(i)
        # Get the defense statistics for these
        # Remember, the a legendary will get a 1.5 times boost vs all regular cards
        other_defs = []
        for i in comp_others:
          if self.all_pokemon_cards[i][1] == 'Legendary':
            other_defs.append(int(self.all_pokemon_cards[i][3]*1.5))
          else:
            other_defs.append(self.all_pokemon_cards[i][3])
        # Get the highest value
        if other_defs:
          other_defs_max = max(other_defs)
        else:
          other_defs_max = 0
        # Now, make the comparison
        if max_electric_def >= other_defs_max:
          # The computer will play its best electric Pokemon
          # Store the card number
          self.declare(ComputerCard(best_electric))
          # Move to the compare types stage
          self.declare(PokemonES('comp_play'))
        else:
          # The computer has a better play than its best electric
          # Get index of its best defense
          best_other_ind = other_defs.index(other_defs_max)
          # Get the Pokemon card number
          best_other = comp_others[best_other_ind]
          # Store the card number
          self.declare(ComputerCard(best_other))
          # Move to the compare types stage
          self.declare(PokemonES('comp_play'))
    
    @Rule(AS.f1 << PokemonES('comp_vs_grass'),
          AS.f2 << ComputerCardTypes(MATCH.c_types),
          AS.f3 << ComputerCards(MATCH.c_cards))
    def comp_vs_grass(self, f1, f2, f3, c_types, c_cards):
        # Here, fire will give a bonus
        # We will see if the computer has any fire Pokemon, calculate the bonus 
        # And then see if it can do better with its other cards.
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        # Get the indexes of all the computer's fire Pokemon
        fire = [i for i,x in enumerate(c_types) if x == 'Fire']
        # For each of these, get corresponding Pokemon
        fire_pokemon = []
        for i in fire:
          fire_pokemon.append(c_cards[i])
        # For each of these, get the defense statistics
        fire_defenses = []
        for i in fire_pokemon:
          fire_defenses.append(self.all_pokemon_cards[i][3])

        # If the computer has fire Pokemon, get the max defense
        if fire_defenses:
          # Get the highest of these fire defense values
          max_fire_def = max(fire_defenses)
          # Get the index of this within this list
          max_fire_def_index = fire_defenses.index(max_fire_def)
          # Get the actual Pokemon card # of this best fire defense
          best_fire = fire_pokemon[max_fire_def_index]
        else:
          # The computer has no fire Pokemon
          max_fire_def = 0
        # We now want to check if the computer has a better option
        # Since fire beats grass, this will be awarded the 1.2 multiplier
        max_fire_def = int(max_fire_def * 1.2)

        # Get the computer's non-fire Pokemon
        comp_others = []
        for i in c_cards:
          if i not in fire_pokemon:
            comp_others.append(i)
        # Get the defense statistics for these
        # Remember, the a legendary will get a 1.5 times boost vs all regular cards
        other_defs = []
        for i in comp_others:
          if self.all_pokemon_cards[i][1] == 'Legendary':
            other_defs.append(int(self.all_pokemon_cards[i][3]*1.5))
          else:
            other_defs.append(self.all_pokemon_cards[i][3])
        # Get the highest value
        if other_defs:
          other_defs_max = max(other_defs)
        else:
          other_defs_max = 0
        # Now, make the comparison
        if max_fire_def >= other_defs_max:
          # The computer will play its best fire Pokemon
          # Store the card number
          self.declare(ComputerCard(best_fire))
          # Move to the compare types stage
          self.declare(PokemonES('comp_play'))
        else:
          # The computer has a better play than its best fire
          # Get index of its best defense
          best_other_ind = other_defs.index(other_defs_max)
          # Get the Pokemon card number
          best_other = comp_others[best_other_ind]
          # Store the card number
          self.declare(ComputerCard(best_other))
          # Move to the compare types stage
          self.declare(PokemonES('comp_play'))
      
    @Rule(AS.f1 << PokemonES('comp_vs_electric'),
          AS.f2 << ComputerCardTypes(MATCH.c_types),
          AS.f3 << ComputerCards(MATCH.c_cards))
    def comp_vs_electric(self, f1, f2, f3, c_types, c_cards):
        # Here, rock will give a bonus
        # We will see if the computer has any rock Pokemon, calculate the bonus 
        # And then see if it can do better with its other cards.
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        # Get the indexes of all the computer's rock Pokemon
        rock = [i for i,x in enumerate(c_types) if x == 'Rock']
        # For each of these, get corresponding Pokemon
        rock_pokemon = []
        for i in rock:
          rock_pokemon.append(c_cards[i])
        # For each of these, get the defense statistics
        rock_defenses = []
        for i in rock_pokemon:
          rock_defenses.append(self.all_pokemon_cards[i][3])

        # If the computer has rock Pokemon, get the max defense
        if rock_defenses:
          # Get the highest of these rock defense values
          max_rock_def = max(rock_defenses)
          # Get the index of this within this list
          max_rock_def_index = rock_defenses.index(max_rock_def)
          # Get the actual Pokemon card # of this best rock defense
          best_rock = rock_pokemon[max_rock_def_index]
        else:
          # The computer has no rock Pokemon
          max_rock_def = 0
        # We now want to check if the computer has a better option
        # Since rock beats electric, this will be awarded the 1.2 multiplier
        max_rock_def = int(max_rock_def * 1.2)

        # Get the computer's non-rock Pokemon
        comp_others = []
        for i in c_cards:
          if i not in rock_pokemon:
            comp_others.append(i)
        # Get the defense statistics for these
        # Remember, the a legendary will get a 1.5 times boost vs all regular cards
        other_defs = []
        for i in comp_others:
          if self.all_pokemon_cards[i][1] == 'Legendary':
            other_defs.append(int(self.all_pokemon_cards[i][3]*1.5))
          else:
            other_defs.append(self.all_pokemon_cards[i][3])
        # Get the highest value
        if other_defs:
          other_defs_max = max(other_defs)
        else:
          other_defs_max = 0
        # Now, make the comparison
        if max_rock_def >= other_defs_max:
          # The computer will play its best rock Pokemon
          # Store the card number
          self.declare(ComputerCard(best_rock))
          # Move to the compare types stage
          self.declare(PokemonES('comp_play'))
        else:
          # The computer has a better play than its best rock
          # Get index of its best defense
          best_other_ind = other_defs.index(other_defs_max)
          # Get the Pokemon card number
          best_other = comp_others[best_other_ind]
          # Store the card number
          self.declare(ComputerCard(best_other))
          # Move to the compare types stage
          self.declare(PokemonES('comp_play'))
      
    @Rule(AS.f1 << PokemonES('comp_vs_rock'),
          AS.f2 << ComputerCardTypes(MATCH.c_types),
          AS.f3 << ComputerCards(MATCH.c_cards))
    def comp_vs_rock(self, f1, f2, f3, c_types, c_cards):
        # Here, grass will give a bonus
        # We will see if the computer has any grass Pokemon, calculate the bonus 
        # And then see if it can do better with its other cards.
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        # Get the indexes of all the computer's grass Pokemon
        grass = [i for i,x in enumerate(c_types) if x == 'Grass']
        # For each of these, get corresponding Pokemon
        grass_pokemon = []
        for i in grass:
          grass_pokemon.append(c_cards[i])
        # For each of these, get the defense statistics
        grass_defenses = []
        for i in grass_pokemon:
          grass_defenses.append(self.all_pokemon_cards[i][3])

        # If the computer has grass Pokemon, get the max defense
        if grass_defenses:
          # Get the highest of these grass defense values
          max_grass_def = max(grass_defenses)
          # Get the index of this within this list
          max_grass_def_index = grass_defenses.index(max_grass_def)
          # Get the actual Pokemon card # of this best grass defense
          best_grass = grass_pokemon[max_grass_def_index]
        else:
          # The computer has no grass Pokemon
          max_grass_def = 0
        # We now want to check if the computer has a better option
        # Since grass beats rock, this will be awarded the 1.2 multiplier
        max_grass_def = int(max_grass_def * 1.2)

        # Get the computer's non-grass Pokemon
        comp_others = []
        for i in c_cards:
          if i not in grass_pokemon:
            comp_others.append(i)
        # Get the defense statistics for these
        # Remember, the a legendary will get a 1.5 times boost vs all regular cards
        other_defs = []
        for i in comp_others:
          if self.all_pokemon_cards[i][1] == 'Legendary':
            other_defs.append(int(self.all_pokemon_cards[i][3]*1.5))
          else:
            other_defs.append(self.all_pokemon_cards[i][3])
        # Get the highest value
        if other_defs:
          other_defs_max = max(other_defs)
        else:
          other_defs_max = 0
        # Now, make the comparison
        if max_grass_def >= other_defs_max:
          # The computer will play its best grass Pokemon
          # Store the card number
          self.declare(ComputerCard(best_grass))
          # Move to the compare types stage
          self.declare(PokemonES('comp_play'))
        else:
          # The computer has a better play than its best grass
          # Get index of its best defense
          best_other_ind = other_defs.index(other_defs_max)
          # Get the Pokemon card number
          best_other = comp_others[best_other_ind]
          # Store the card number
          self.declare(ComputerCard(best_other))
          # Move to the compare types stage
          self.declare(PokemonES('comp_play'))
    
    @Rule(AS.f1 << PokemonES('comp_vs_legendary'),
          AS.f2 << ComputerCardTypes(MATCH.c_types),
          AS.f3 << ComputerCards(MATCH.c_cards))
    def comp_vs_legendary(self, f1, f2, f3, c_types, c_cards):
        # Here, there is no bonus to be had
        # A legendary Pokemon will counter the user's legendary, so we will check 
        # 1.5 times that defense against the other defense statistics
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        # Get all the defense statistics
        comp_defenses = []
        for card in c_cards:
          if self.all_pokemon_cards[card][1] == 'Legendary':
            comp_defenses.append(int(self.all_pokemon_cards[card][3]*1.5))
          else:
            comp_defenses.append(self.all_pokemon_cards[card][3])
        # Get the maximum value
        max_def = max(comp_defenses)
        # Get the index of this
        best_index = comp_defenses.index(max_def)
        # Get the Pokemon number
        best_def = c_cards[best_index]
        # Store the card number
        self.declare(ComputerCard(best_def))
        # Move to the compare types stage
        self.declare(PokemonES('comp_play')) 
        
    @Rule(AS.f1 << PokemonES('comp_play'),
          AS.f2 << ComputerCard(MATCH.c_card))
    def comp_play_second(self, f1, f2, c_card):
      self.retract(f1)
      # Display the computer's choice
      print('\nComputer plays {}!'.format(self.all_pokemon_cards[c_card][0]))
      print('Type: {}, Attack: {}, Defense: {}'.format(self.all_pokemon_cards[c_card][1], 
                                                             self.all_pokemon_cards[c_card][2], 
                                                             self.all_pokemon_cards[c_card][3]))
      self.declare(PokemonES('compare_types'))


    ####  
    #
    # CASE 2:  the computer goes first (even numbered rounds)
    #
    ####
    @Rule(AS.f1 << PokemonES('computer_plays_first'),
          AS.f2 << ComputerAttackDifficulty(diff=MATCH.c_diff))
    def computer_plays_first(self, f1, f2, c_diff):
      self.retract(f1)
      # If the user selected 0, the computer will attack by selecting random cards
      if c_diff == 0:
        self.declare(PokemonES('comp_attack_random'))
      else:
        # Otherwise, the computer will look at its cards and choose the best one 
        self.declare(PokemonES('comp_attack_optimal'))
    
    @Rule(AS.f1 << PokemonES('comp_attack_random'),
          AS.f2 << ComputerCards(MATCH.c_cards))
    def comp_attack_random(self, f1, f2, c_cards):
      self.retract(f1)
      self.retract(f2)
      # Get the list of card numbers 
      c_cards = list(c_cards)
      # Make a random choice
      c_choice = int(random.choice(c_cards))
      # Get the Pokemon name
      c_card = self.all_pokemon_cards[c_choice][0]
      # Display the information for the user
      print('\nComputer plays {}!'.format(c_card))
      print('Type: {}, Attack: {}, Defense: {}'.format(self.pokemon_cards[c_choice][1], 
                                                             self.pokemon_cards[c_choice][2], 
                                                             self.pokemon_cards[c_choice][3]))
      # Store the computer's choice
      self.declare(ComputerCard(c_choice))
      # Move to the user
      self.declare(PokemonES('user_plays_second'))    
    
    ###
    # 
    # THE COMPUTER WILL PLAY A LEGENDARY CARD, IF IT HAS ONE.
    # IF NOT, IT WILL PLAY THE CARD WITH THE BEST ATTACK.
    #
    ###
    @Rule(AS.f1 << PokemonES('comp_attack_optimal'),
         AS.f2 << ComputerCards(MATCH.c_cards))
    def comp_attack_optimal(self, f1, f2, c_cards):
        self.retract(f1)
        # Get the types of the computer's cards
        comp_types = []
        for card in c_cards:
          comp_types.append(self.all_pokemon_cards[card][1])
        # If the computer has a legendary card, it will play it
        if 'Legendary' in comp_types:
          self.retract(f2)
          leg_ind = comp_types.index('Legendary')
          # Get the card number
          c_card = c_cards[leg_ind]
          # Display the info for the user
          print('\nComputer plays {}!'.format(self.all_pokemon_cards[c_card][0]))
          print('Type: {}, Attack: {}, Defense: {}'.format(self.all_pokemon_cards[c_card][1], 
                                                             self.all_pokemon_cards[c_card][2], 
                                                             self.all_pokemon_cards[c_card][3]))
          # Store the computer's choice
          self.declare(ComputerCard(c_card))
          # Move to the user
          self.declare(PokemonES('user_plays_second'))
        else:
          self.declare(PokemonES('comp_plays_no_legendary'))
      
    @Rule(AS.f1 << PokemonES('comp_plays_no_legendary'),
          AS.f2 << ComputerCards(MATCH.c_cards))
    def comp_plays_first_no_legendary(self, f1, f2, c_cards):
        self.retract(f1)
        self.retract(f2)
        # The computer will play the card with the highest attack value
        comp_attacks = []
        for card in c_cards:
          comp_attacks.append(self.all_pokemon_cards[card][2])
        # Get the highest value
        max_attack = max(comp_attacks)
        # Get the index of this
        max_ind = comp_attacks.index(max_attack)
        # Get the corresponding Pokemon card number
        c_card = c_cards[max_ind]
        # Display information for the user
        print('\nComputer plays {}!'.format(self.all_pokemon_cards[c_card][0]))
        print('Type: {}, Attack: {}, Defense: {}'.format(self.all_pokemon_cards[c_card][1], 
                                                             self.all_pokemon_cards[c_card][2], 
                                                             self.all_pokemon_cards[c_card][3]))
        # Store the computer's choice
        self.declare(ComputerCard(c_card))
        # Move to the user
        self.declare(PokemonES('user_plays_second'))
    
    # The user sees the computer's play and it is now their turn
    @Rule(AS.f1 << PokemonES('user_plays_second'),
         AS.f2 << UserCards(MATCH.u_cards))
    def user_plays_second(self, f1, f2, u_cards):
        self.retract(f1)
        self.retract(f2)
        print('\nIt\'s your turn.')
        print('You are on the DEFENSE!') 
        print('\nSelect a card to play.')
        # Get the user's choice - ensuring it is a card they have
        while True:
            choice = int(input('Enter card number: '))
            if choice in list(u_cards):
                break
            else:
                print('You don\'t have that card!')
        print('\nYou play {}!'.format(self.all_pokemon_cards[choice][0]))
        # Store user choice
        self.declare(UserCard(choice))
        # Store the type of the user's card
        u_type = self.all_pokemon_cards[choice][1]
        self.declare(UserCardType(u_type))
        # Move onto comparing the types
        self.declare(PokemonES('compare_types'))
    
    # Comparing Pokemon types
    # This will determine the multiplier bonus
    @Rule(AS.f1 << PokemonES('compare_types'),
          AS.f2 << UserCardType(MATCH.u_type),
          AS.f3 << ComputerCard(MATCH.c_card))
    def compare_types(self, f1, f2, f3, u_type, c_card):
        self.retract(f1)
        # Get the computer's card type
        c_type = self.all_pokemon_cards[c_card][1]
        print('\nYour Pokemon type is {}.'.format(u_type.upper()))
        print("The computer's Pokemon type is {}.".format(c_type.upper()))
        self.declare(ComputerCardType(c_type))

        if u_type == 'Legendary' and c_type == 'Legendary':
          self.declare(PokemonES('both_legendary'))
        elif u_type == 'Legendary' and c_type != 'Legendary':
          self.declare(PokemonES('user_legendary'))
        elif u_type != 'Legendary' and c_type == 'Legendary':
          self.declare(PokemonES('comp_legendary'))
        else:
          self.declare(PokemonES('no_legendary'))
    
    @Rule(AS.f1 << PokemonES('both_legendary'),
          AS.f2 << UserCardType(MATCH.u_type),
          AS.f3 << ComputerCardType(MATCH.c_type))
    def both_legendary(self, f1, f2, f3, u_type, c_type):
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        bonus = None
        # Store which player received the bonus
        self.declare(WhoGetsMultiplier(bonus))
        print('Two legendary Pokemon! There is no bonus.')
        # Store the multiplier value
        multiplier = 1
        self.declare(Multiplier(multiplier))
        # Move next to the battle
        self.declare(PokemonES('battle'))
    
    @Rule(AS.f1 << PokemonES('user_legendary'),
          AS.f2 << UserCardType(MATCH.u_type),
          AS.f3 << ComputerCardType(MATCH.c_type))
    def user_legendary(self, f1, f2, f3, u_type, c_type):
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        bonus = 'user_legendary'
        # Store which player received the bonus
        self.declare(WhoGetsMultiplier(bonus))
        print('You get a large boost!')
        # Store the multiplier value
        multiplier = 1.5
        self.declare(Multiplier(multiplier))
        # Move next to the battle
        self.declare(PokemonES('battle'))
    
    @Rule(AS.f1 << PokemonES('comp_legendary'),
          AS.f2 << UserCardType(MATCH.u_type),
          AS.f3 << ComputerCardType(MATCH.c_type))
    def comp_legendary(self, f1, f2, f3, u_type, c_type):
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        bonus = 'comp_legendary'
        # Store which player received the bonus
        self.declare(WhoGetsMultiplier(bonus))
        print('The computer gets a large boost!')
        # Store the multiplier value
        multiplier = 1.5
        self.declare(Multiplier(multiplier))
        # Move next to the battle
        self.declare(PokemonES('battle'))

    @Rule(AS.f1 << PokemonES('no_legendary'),
          AS.f2 << UserCardType(MATCH.u_type),
          AS.f3 << ComputerCardType(MATCH.c_type))
    def no_legendary(self, f1, f2, f3, u_type, c_type):
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        # Make the comparisons
        if u_type == 'Fire':
          if c_type == 'Grass':
            bonus = 'user'
          elif c_type == 'Water':
            bonus = 'computer'
          else:
            bonus = None
        
        elif u_type == 'Water':
          if c_type == 'Fire':
            bonus = 'user'
          elif c_type == 'Electric':
            bonus = 'computer' 
          else:
            bonus = None         

        elif u_type == 'Grass':
          if c_type == 'Rock':
            bonus = 'user'
          elif c_type == 'Fire':
            bonus = 'computer'
          else:
            bonus = None 

        elif u_type == 'Rock':
          if c_type == 'Electric':
            bonus = 'user'
          elif c_type == 'Grass':
            bonus = 'computer'
          else:
            bonus = None

        elif u_type == 'Electric':
          if c_type == 'Water':
            bonus = 'user'
          elif c_type == 'Rock':
            bonus = 'computer'
          else:
            bonus = None

        # Set the bonus value
        multiplier = 1.2
        # Store which player received the bonus
        self.declare(WhoGetsMultiplier(bonus))
        # Store the multiplier value
        self.declare(Multiplier(multiplier))
        # Print the bonus status
        if bonus == 'user':
          print('\nYou get a boost!')
        elif bonus == 'computer':
          print('\nThe computer gets a boost!')
        else:
          print('There is no bonus.')
        
        # Move next to the battle
        self.declare(PokemonES('battle'))
    
    # We are now ready to determine the damage done in the round
    # We need the card selections, bonus information, and the round number
    # Round number is being used to keep track of who plays first in the round
    @Rule(AS.f1 << PokemonES('battle'), 
          AS.f2 << UserCard(MATCH.u_card),
          AS.f3 << ComputerCard(MATCH.c_card),
          AS.f4 << WhoGetsMultiplier(MATCH.bonus),
          AS.f5 << Multiplier(MATCH.multiplier),
          AS.f6 << HP(user=MATCH.uhp, computer=MATCH.chp), 
          RoundNumber(round_num=MATCH.rnum))
    def battle(self, f1, f2, f3, f4, f5, f6, u_card, c_card, bonus, multiplier, uhp, chp, rnum):
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        self.retract(f4)
        self.retract(f5)
        # Do not retract HP and round numbers - these will be updated at the 
        # end of the round
        ###
        #
        # FOR NOW: whoever goes first, always attacks
        # Other player always defends
        # User goes first on odd numbered rounds
        ###
        print('.....................')
        print('BATTLE!')
        print('.....................')
        # On odd rounds, the user goes first
        if rnum%2 != 0:
            # Get the attack value of their chosen card
            u_attack = self.all_pokemon_cards[u_card][2]
            # Get the computer's defense
            c_defense = self.all_pokemon_cards[c_card][3]
            if bonus == 'user':
                u_attack = int(u_attack * multiplier)
            elif bonus == 'user_legendary':
                u_attack = int(u_attack * multiplier)
            elif bonus == 'computer':
                c_defense = int(c_defense * multiplier)
            elif bonus == 'comp_legendary':
                c_defense = int(c_defense * multiplier)
            # Display the attack and defense stats with bonus awarded
            print('\nYou attack with', u_attack)
            print('The computer defends with', c_defense) 
            # Check how user's attack does against computer's defense
            difference = u_attack - c_defense
            # If attack is higher than defense, user is successful
            if difference > 0:
                print('\nSuccess! You did {} damage!'.format(difference))
                # Remove the damage from the computer's CURRENT overall HP
                chp = chp - difference
            elif difference == 0:
                print('A perfect matchup. No damage!')
            else:
                # If defense is stronger, the user uses the damage
                # NOTE:  here difference is a negative number
                print('\nYour attack was defended! You lost {} HP!'.format(abs(difference)))
                uhp = uhp + difference
        
        # On even numbered rounds, the computer goes first
        else:
            # As above, award bonus
            c_attack = self.all_pokemon_cards[c_card][2]
            u_defense = self.all_pokemon_cards[u_card][3]
            if bonus == 'computer':
                c_attack = int(c_attack * multiplier)
            elif bonus == 'comp_legendary':
                c_attack = int(c_attack * multiplier)
            elif bonus == 'user':
                u_defense = int(u_defense * multiplier)
            elif bonus == 'user_legendary':
                u_defense = int(u_defense * multiplier)
        
            print('\nThe computer attacks with', c_attack)
            print('You defend with', u_defense)           
            
            # See if computer's attack is successful
            difference = c_attack - u_defense
            if difference > 0:
                print('\nThe computer did {} damage to you!'.format(difference))
                uhp = uhp - difference 
            elif difference == 0:
                print('A perfect matchup. No damage!')
            else:
                print('\nYou defended the attack! The computer lost {} HP!'.format(abs(difference)))
                chp = chp + difference 

        # Modify the fact to update the overall HP standings for both players
        self.modify(f6, user=uhp, computer=chp)        
        
        # We are continuing the game until one of the players reaches zero HP
        # Check if that has happened in this round
        if uhp <= 0 or chp <=0:
            # If it has, move to end game
            self.declare(PokemonES('end_game'))
        else:
            # If it hasn't, start a new round
            self.declare(PokemonES('next_round'))
    
    # As the game continues, we start a new round 
    # All new cards will be dealt 
    @Rule(AS.f1 << PokemonES('next_round'),
          AS.f2 << RoundNumber(round_num=MATCH.rnum))
    def next_round(self, f1, f2, rnum):   
        self.retract(f1)
        print('\nLet\'s go again!')
        # Update the round number fact 
        self.modify(f2, round_num=rnum+1)
        # Move to the show_scores function that begins the round
        # Round and scores and displayed and the game is repeated 
        self.declare(PokemonES('show_scores'))
    
    # We reach here when one of the players has reached zero HP            
    @Rule(AS.f1 << PokemonES('end_game'), 
          AS.f2 << HP(user=MATCH.uhp, computer=MATCH.chp))
    def end_the_game(self, f1, f2, uhp, chp):
        self.retract(f1)
        self.retract(f2)
        # If it is the computer that has reached zero, the player wins
        if chp <=0:
            print('\nYou win!')
            print('You are a Pokemon Master :)!')
        else:
            print('\nYou lost!')
            print('Better luck next time!')

# Initialize the knowledge engine
game = PlayPokemonES()
# Reset and run
game.reset()
game.run()

game.facts

