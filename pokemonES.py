import pandas as pd
from pyknow import *
import random

df = pd.read_excel('Pokemon 5 Types_Updated.xlsx', sheet_name='Pokemon 5 types')
# Using only the regular Pokemon for now
regular_pokemon = df[df['Legendary']==False]

# The Fact Subclases

class PokemonES(Fact):
    """
    Holds game Facts (moving from rule to rule)
    """
    pass

class PokemonCards(Fact):
    """
    Info about the cards in the deck
    """
    p_key = Field(int, mandatory=True)
    p_name = Field(str, mandatory=True)
    p_type = Field(str, mandatory=True)
    p_attack = Field(int, mandatory=True)
    p_defense = Field(int, mandatory=True)

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

class ComputerCard(Fact):
    """
    The computer's choice for the round
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
        # Dictionary of avaiable Pokemon 
        self.pokemon_cards = dict()
        for i in range(len(regular_pokemon)):
            yield PokemonCards(p_key = int(regular_pokemon['#'][i]), p_name=regular_pokemon['Name'][i], 
                               p_type=regular_pokemon['Type 1'][i], p_attack=int(regular_pokemon['Attack'][i]), 
                               p_defense=int(regular_pokemon['Defense'][i]))
    
    # Store the dictionary of pokemon cards
    @Rule(NOT(PokemonES()), PokemonCards(p_key=MATCH.p_key, p_name=MATCH.name, p_type=MATCH.p_type, 
                                         p_attack=MATCH.attack, p_defense=MATCH.defense))
    def def_pokemon_cards(self, p_key, name, p_type, attack, defense):
          self.pokemon_cards[p_key] = [name, p_type, attack, defense]
    
    # Define what happens when the game is started
    @Rule()
    def new_game(self):
        print('Let\'s play Pokemon!')
        # Set the starting values for user and computer's HP
        self.declare(HP(user=200, computer=200))
        # Reset to start at round one
        self.declare(RoundNumber(round_num=1))
        # Move to next rule
        self.declare(PokemonES('show_scores'))
    
    # This is where we will begin each round as the game progresses 
    # Showing scores and round number
    @Rule(AS.f1 << PokemonES('show_scores'), 
          AS.f2 << HP(user=MATCH.uhp,
            computer=MATCH.chp), 
          AS.f3 << RoundNumber(round_num=MATCH.rnum))
    def print_current_scores(self, f1, f2, f3, uhp, chp, rnum):
        self.retract(f1)
        # NOTE: we do not retract HP and Round Number because these are being maintained 
        # throughout the game
        print('Round:', rnum)
        print('\nCurrent HP: ')
        print('You:', uhp)
        print('Computer:', chp)
        self.declare(PokemonES('deal'))
        
    # Deal cards to user and computer
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
        
    # Show the user their cards
    @Rule(AS.f1 << PokemonES('show_user_cards'), UserCards(MATCH.u_cards))
    def show_user_cards(self, f1, u_cards):
        self.retract(f1)
        print('\nHere are your cards!')
        print('.....................')
        # Print the user their available cards, along with the attributes of each
        for i in u_cards:
            print(i, self.pokemon_cards[i][0])
            print('Type: {}, Attack: {}, Defense: {}'.format(self.pokemon_cards[i][1], 
                                                             self.pokemon_cards[i][2], 
                                                             self.pokemon_cards[i][3]))
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
    
    #
    # CASE 1:  the player goes first (odd numbered rounds)
    #
    
    # When the player goes first, they are free to play any card they wish
    @Rule(AS.f1 << PokemonES('user_plays_first'), 
          AS.f2 << UserCards(MATCH.u_cards))
    def user_plays_first(self, f1, f2, u_cards):
        self.retract(f1)
        # We are finished with the user's set of cards for this round
        self.retract(f2)
        print('It\'s your turn. Select a card to play.')
        # We get the user's selection
        # We handle if they enter a value corresponding to a card they do not have 
        while True:
            choice = int(input('Enter card number: '))
            if choice in list(u_cards):
                break
            else:
                print('You don\'t have that card!')
        print('\nYou play {}!'.format(self.pokemon_cards[choice][0]))
        # Store the user's selection and move to computer
        self.declare(UserCard(choice))
        self.declare(PokemonES('computer_plays_second'))
    
    ###
    # COMPUTER PLAYS SECOND
    # HERE WE WILL HAVE ALL OF OUR RULES FOR THE EXPERT SYSTEM
    # SO THAT THE COMPUTER PLAYS THE BEST POSSIBLE CARD GIVEN
    # WHAT THE USER HAS PLAYED
    #
    #
    #
    #
    #
    #
    # FOR NOW, COMPUTER WILL PLAY A RANDOM CARD
    #
    #
    #
    #
    ###
    @Rule(AS.f1 << PokemonES('computer_plays_second'),
         AS.f2 << ComputerCards(MATCH.c_cards))
    def computer_plays_second(self, f1, f2, c_cards):
        self.retract(f1)
        self.retract(f2)
        c_cards = list(c_cards)
        choice = int(random.choice(c_cards))
        c_card = self.pokemon_cards[choice][0]
        # Display the computer's choice 
        print('\nComputer plays {}!'.format(c_card))
        print('Type: {}, Attack: {}, Defense: {}'.format(self.pokemon_cards[choice][1], 
                                                             self.pokemon_cards[choice][2], 
                                                             self.pokemon_cards[choice][3]))
        # Store the computer's choice
        self.declare(ComputerCard(choice))
        # Now that the player and computer have chose, we compare the types
        self.declare(PokemonES('compare_types'))
      
    #
    # CASE 2:  the computer goes first (even numbered rounds)
    #
    
    ###
    # HERE WE HAVE TO DECIDE HOW THE COMPUTER WILL CHOOSE THEIR CARD WHEN THEY PLAY FIRST
    # WILL IT BE RANDOM?
    # HIGHEST ATTACK?
    #
    #
    # FOR NOW THE COMPUTER WILL JUST PLAY A RANDOM CARD
    #
    #
    ###
    @Rule(AS.f1 << PokemonES('computer_plays_first'),
         AS.f2 << ComputerCards(MATCH.c_cards))
    def computer_plays_first(self, f1, f2, c_cards):
        self.retract(f1)
        self.retract(f2)
        # Play a random card
        c_cards = list(c_cards)
        choice = int(random.choice(c_cards))
        c_card = self.pokemon_cards[choice][0]
        # Display information for the user
        print('\nComputer plays {}!'.format(c_card))
        print('Type: {}, Attack: {}, Defense: {}'.format(self.pokemon_cards[choice][1], 
                                                             self.pokemon_cards[choice][2], 
                                                             self.pokemon_cards[choice][3]))
        # Store the computer's choice
        self.declare(ComputerCard(choice))
        # Move to the user
        self.declare(PokemonES('user_plays_second'))
    
    # The user sees the computer's play and it is now their turn
    @Rule(AS.f1 << PokemonES('user_plays_second'),
         AS.f2 << UserCards(MATCH.u_cards))
    def user_plays_second(self, f1, f2, u_cards):
        self.retract(f1)
        self.retract(f2)
        print('\nIt\'s your turn. Select a card to play.')
        # Get the user's choice - ensuring it is a card they have
        while True:
            choice = int(input('Enter card number: '))
            if choice in list(u_cards):
                break
            else:
                print('You don\'t have that card!')
        print('\nYou play {}!'.format(self.pokemon_cards[choice][0]))
        # Store user choice
        self.declare(UserCard(choice))
        # Move onto comparing the types
        self.declare(PokemonES('compare_types'))
    
    # Comparing Pokemon types
    # This will determine the multiplier bonus
    @Rule(AS.f1 << PokemonES('compare_types'),
         AS.f2 << UserCard(MATCH.u_card),
          AS.f3 << ComputerCard(MATCH.c_card))
    def compare_types(self, f1, f2, f3, u_card, c_card):
        self.retract(f1)
        # We will continue to need the chosen cards, so do not retract the facts
        
        ###
        # PRINTING JUST TO SEE WHERE WE ARE AND TO MAKE THE COMPARISON
        ###
        print('\nYou have a {} Pokemon.'.format(self.pokemon_cards[u_card][1]))
        print('The computer has a {} Pokemon.'.format(self.pokemon_cards[c_card][1]))
        
        ###
        # HERE WE HAVE TO DEFINE THE MULTIPLIERS BASED ON THE TWO TYPES
        # WILL WE JUST CODE IN WITH IF-STATEMENTS????
        ###
        # For now, just assign the bonus to the user
        bonus = 'user' # or 'computer'
        # Set a bonus value for now
        multiplier = 1.2
        # Store which player received the bonus
        self.declare(WhoGetsMultiplier(bonus))
        # Store the multiplier value
        self.declare(Multiplier(multiplier))
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
        #
        # WE CAN ADD IN THE CHOICE LATER
        # HOW WILL COMPUTER DECIDE WHAT TO DO???
        #
        #
        ###
        print('.....................')
        print('BATTLE!')
        print('.....................')
        # On odd rounds, the user goes first
        if rnum%2 != 0:
            # Get the attack value of their chosen card
            u_attack = self.pokemon_cards[u_card][2]
            if bonus == 'user':
                # If user has the bonus, award it to their attack
                print('You earn the bonus!')
                u_attack = int(u_attack * multiplier)
                # Get the computer's card's defense stat
                c_defense = self.pokemon_cards[c_card][3]
            else:
                # Award the bonus to the computer if it is theirs
                print('Computer earns the bonus!')
                u_attack = self.pokemon_cards[u_card][3]
                c_defense = int(self.pokemon_cards[c_card][3] * multiplier)
            # Display the attack and defense stats with bonus awarded
            print('\nYou attack with', u_attack)
            print('The computer defends with', c_defense) 
            # Check how user's attack does against computer's defense
            difference = u_attack - c_defense
            # If attack is higher than defense, user is successful
            if difference >= 0:
                print('\nSuccess! You did {} damage!'.format(difference))
                # Remove the damage from the computer's CURRENT overall HP
                chp = chp - difference
            else:
                # If defense is stronger, the user uses the damage
                # NOTE:  here difference is a negative number
                print('\nYour attack was defended! You lost {} HP!'.format(abs(difference)))
                uhp = uhp + difference
        
        # On even numbered rounds, the computer goes first
        else:
            # As above, award bonus
            c_attack = self.pokemon_cards[c_card][2]
            if bonus == 'computer':
                print('Computer earns the bonus!')
                u_defense = self.pokemon_cards[u_card][3]
                c_attack = int(c_attack * multiplier)
            else:
                print('You earn the bonus!')
                u_defense = int(self.pokemon_cards[u_card][3] * multiplier)
                c_attack = self.pokemon_cards[c_card][2]
            
            print('\nThe computer attacks with', c_attack)
            print('You defend with', u_defense)           
            
            # See if computer's attack is successful
            difference = c_attack - u_defense
            if difference >= 0:
                print('\nThe computer did {} damage to you!'.format(difference))
                uhp = uhp - difference 
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
            print('You win!')
            print('You are a Pokemon Master :)!')
        else:
            print('You lost!')
            print('Better luck next time!')

# Initialize the knowledge engine
game = PlayPokemonES()
# Reset and run
game.reset()
game.run()