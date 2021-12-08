# get the published TX(function hasn't been thought)
# Assuming we have obtained the tx
__all__ = [
  'parseTxtoGetTargetID'
]

def parseTxtoGetTargetID(tx):
    """
    Generally speaking, tx is in dictionary format
    Temporarily, name the key value of the target ID as targetID 
    """
    targetID = tx.get("targetID")
    return targetID
