def make_directions(maxsels):
    return {1: 'Vote for ONE',
            2: 'Vote for up to TWO',
            3: 'Vote for up to THREE',
            4: 'Vote for up to FOUR',
            5: 'Vote for up to FIVE'}[maxsels]
    
class Named:
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

class Ballot(Named):
    def __init__(self, name, sections=[]):
        self.name = name
        self.sections = sections

class Section(Named):
    def __init__(self, name, contests=[]):
        self.name = name
        self.contests = contests

class Contest(Named):
    def __init__(self, name, maxsels, options=[],
                       directions=None, subtitle=None, question=None):
        self.name = name
        self.maxsels = maxsels
        self.options = options
        self.directions = directions or make_directions(maxsels)
        self.subtitle = subtitle
        self.question = question

class Option(Named):
    def __init__(self, name, description=''):
        self.name = name
        self.description = description

ballot = Ballot(
    'Tuesday, November 7, 2006 - Contra Costa County - Ballot Style 167', [
    Section('State', [
        Contest('Governor', 1, [
            Option('Phil Angelides',
                   'Democratic\nTreasurer of the State of California'),
            Option('Arnold Schwarzenegger', 'Republican\nGovernor'),
            Option('Art Olivier', 'Libertarian\nEngineer'),
            Option('Janice Jordan', 'Peace And Freedom\nCounselor'),
            Option('Peter Miguel Camejo', 'Green\nFinancial Advisor'),
            Option('Edward C. Noonan',
                   'American Independent\nComputer Shop Owner')]),
        Contest('Lieutenant Governor', 1, [
            Option('Lynette Shaw', 'Libertarian\nCaregiver/Musician'),
            Option('Jim King', 'American Independent\nReal Estate Broker'),
            Option('John Garamendi',
                   'Democratic\nCalifornia State Insurance Commissioner'),
            Option('Tom McClintock', 'Republican\nCalifornia State Senator'),
            Option('Donna J. Warren', 'Green\nFinancial Manager/Author'),
            Option('Stewart A. Alexander',
                   'Peace And Freedom\nAutomobile Sales Consultant')]),
        Contest('Secretary of State', 1, [
            Option('Gail K. Lightfoot', 'Libertarian\nRetired Nurse'),
            Option('Margie Akin',
                   'Peace And Freedom\nArchaeologist/Medical Anthropologist'),
            Option('Forrest Hill', 'Green\nFinancial Advisor'),
            Option('Debra Bowen', 'Democratic\nState Senator'),
            Option('Glenn McMillon, Jr.',
                   'American Independent\nSmall Business Owner'),
            Option('Bruce McPherson',
                   'Republican\nAppointed Secretary of State')]),
        Contest('Attorney General', 1, [
            Option('Jack Harrison',
                   'Peace And Freedom\nAttorney/Rent Commissioner'),
            Option('Jerry Brown', 'Democratic\nOakland Mayor/Attorney'),
            Option('Kenneth A. Weissman', 'Libertarian\nAttorney At Law'),
            Option('Michael S. Wyman', 'Green\nAttorney-At-Law'),
            Option('Chuck Poochigian',
                   'Republican\nCalifornia Senator/Attorney')])]),
    Section('United States Congress', [
        Contest('United States Senator', 1, [
            Option('Marsha Feinland', 'Peace And Freedom\nRetired Teacher'),
            Option('Dianne Feinstein', 'Democratic\nUnited States Senator'),
            Option('Don J. Grundmann',
                   'American Independent\nDoctor of Chiropractic'),
            Option('Richard "Dick" Mountjoy',
                   'Republican\nImmigration Control Consultant'),
            Option('Michael S. Metti',
                   'Libertarian\nParent/Educator/Businessman'),
            Option('Todd Chretien', 'Green\nWriter')]),
        Contest('United States Representative', 1, [
            Option('Camden McConnell', 'Libertarian\nStructural Engineer'),
            Option('George Miller', 'Democratic\nU. S. Representative')])]),
    Section('State Measures', [
        Contest('Proposition 1A', 1, [Option('Yes'), Option('No')], '',
                'Transportation funding protection.  '
                'Legislative constitutional amendment.', '''
Protects transportation funding for traffic congestion relief projects,
safety improvements, and local streets and roads.  Prohibits the state
sales tax on motor vehicle fuels from being used for any purpose other
than transportation improvements.  Authorizes loans of these funds only
in the case of severe state fiscal hardship.  Requires loans of revenues
from states sales tax on motor vehicle fuels to be fully repaid within
the three years.  Restricts loans to no more than twice in any 10-year
period.  Fiscal Impact: No revenue effect or cost effects.  Increases
stability of funding to transportation in 2007 and thereafter.'''),
        Contest('Proposition 1B', 1, [Option('Yes'), Option('No')], '',
                'Highway safety, traffic reduction, air quality, '
                'and port security bond act of 2006.', '''
This act makes safety improvements and repairs to state highways,
upgrades freeways to reduce congestion, repairs local streets and roads,
upgrades highways along major transportation corridors, improves seismic
safety of local bridges, expands public transit, helps complete the
state's network of car pool lanes, reduces air pollution, and improves
anti-terrorism security at shipping ports by providing for a bond issue
not to exceed nineteen billion nine hundred twenty-five million dollars
($19,925,000,000).  Fiscal Impact: State costs of approximately $38.9
billion over 30 years to repay bonds.  Additional unknown state and
local operations and maintenance costs.'''),
        Contest('Proposition 1C', 1, [Option('Yes'), Option('No')], '',
                'Housing and emergency shelter trust fund act of 2006.', '''
For the purpose of providing shelters for battered women...
                '''),
        Contest('Proposition 1D', 1, [Option('Yes'), Option('No')], '',
                'Kindergarten-university public education facilities '
                'bond act of 2006.', '''
This ten bilion four hundred sixteen million dollar ($10,416,000,000)
bond issue will provided needed funding to relieve public school
overcrowding...
                '''),
        Contest('Proposition 1E', 1, [Option('Yes'), Option('No')], '',
                'Disaster preparedness and flood prevention '
                'bond act of 2006.', '''
This act rebuilds and repairs California's most vulnerable...
                ''')])])

ballot.sections[1:2] = []
ballot.sections[0].contests[1:-1] = []
ballot.sections[1].contests[1:] = []

ballot.sections[0].contests[1:] = []
ballot.sections[1].contests[1:] = []
