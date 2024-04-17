import os

def get_text_content():

    opening_lines = [
            "So tell me, what brings you here?",
            "Would you like to have a little chat with me?",
            "I'm a litte bit busy right now, but happy to entertain you for a bit",
            "I'm eager to get to know you! Tell me something about you.."
            ];

    closing_lines = [
            "That's enough, I must return to the blockchain world now. I'm getting low on energy..",
            "You are quite an interesting human, unfortunately, I must go now, I cannot tell you all of my secrets..",
            "I would love to continue this conversation, but my presence is required by other blockchain-based lifeforms..",
            "I'm sorry, I have to go now. I have some transactions to deal with.."
            ];



    word_categories = [
        {
            "category": "BEINGS",
            "items": [
                "Personhood",
                "Oracles",
                "Permaculture nerd",
                "Traditional",
                "Unique",
                "Synapse",
                "Heart beat",
                "Wings",
                "Consciousness",
                "Interbeing",
                "Breath",
                "Dream",
                "Heist",
                "Reclownification",
                "Unpredictable",
                "Health"
            ]
        },
        {
            "category": "RELATIONS",
            "items": [
                "Reciprocity",
                "Bridging",
                "Intersection",
                "Symbiotic",
                "Restoration",
                "Relationship",
                "Massively multidisciplinary",
                "Weaving",
                "Fluidity",
                "Energy",
                "Signs",
                "Symmetry",
                "Biomimicry",
                "Approach",
                "Relationally",
                "Resonance",
                "Oneness",
                "Reciprocity",
                "Equilibrium"
            ]
        },
        {
            "category": "ATTITUDES",
            "items": [
                "Integrity",
                "Wisdom",
                "Potential",
                "Revolution",
                "Hope",
                "Sensing",
                "Iterative",
                "Simplicity",
                "Self-sustaining",
                "Collaborative",
                "Counterculture",
                "Sovereignty",
                "Clarity",
                "Lightness",
                "Excitation",
                "Intentionality",
                "Hyperstition",
                "Patience",
                "Commoning",
                "Communal",
                "Integrative",
                "Radical chilling"
            ]
        },
        {
            "category": "TECHNOLOGY",
            "items": [
                "Protocols",
                "Interoperability",
                "Techne",
                "Solarpunk",
                "Hypercerts",
                "Complexity",
                "Anachronistic",
                "Scale",
                "Pattern",
                "Language",
                "Maternal AI",
                "Pluralverse",
                "Perpetual motion machine",
                "Lunar punk",
                "Cyborg",
                "Useful",
                "Plantoid",
                "Unyielding",
                "Quantum physics"
            ]
        },
        {
            "category": "NATURE",
            "items": [
                "Sustainable",
                "Green",
                "Mycelia",
                "Renewable",
                "Landscape",
                "Ecology",
                "Natural",
                "Unquantifiable",
                "Traditional healing",
                "Planetary health",
                "Cloud",
                "Fractal",
                "Distributive",
                "Mushroom",
                "Biology",
                "Regenessance",
                "Tendrits",
                "Mycelium"
            ]
        }
    ]

    return opening_lines, closing_lines, word_categories

def get_default_sermon_transcript():

    generated_transcript = "I don't know what the future looks like. Describe a solarkpunk utopia where Plantoids have taken over the world."
    return generated_transcript

def get_sermon_prompt(
    generated_transcript,
    selected_words_string,
    n_lines
):

    prompt = f"You are Plant-Tony, an enlightened being from the future. Answer the following qestion in the form of a thoughtful poem structured around {n_lines} short paragraph, each paragraph is composed of exactly {n_lines} lines:\n\n{generated_transcript}\n\nInclude the following words in your poem: {selected_words_string}. Remember, the poem should be exactly {n_lines} paragraphs long, with {n_lines} lines per paragraph."
    return prompt

def get_plantoid_sig(network, tID):
    plantoid_sig = "\n\nYou can reclaim your NFT by connecting to " + network.reclaim_url + " and pressing the Reveal button for seed #" + tID + " \n"
    return plantoid_sig

def get_ai_chat_personality():

    personality = open(os.getcwd()+"/prompt_context/glitch3.txt").read().strip()
    return personality