# The MIT License (MIT)
# Copyright © 2023 Yuma
# developer: dubm
# Copyright © 2023 Natix

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import os
import time

import bittensor as bt
import wandb
import yaml

import natix
from natix.base.validator import BaseValidatorNeuron
from natix.validator.cache import ImageCache
from natix.validator.config import (
    CLEAR_IMAGE_CACHE_DIR,
    I2I_CACHE_DIR,
    MAINNET_UID,
    MAINNET_WANDB_PROJECT,
    ROADWORK_IMAGE_CACHE_DIR,
    T2I_CACHE_DIR,
    TESTNET_WANDB_PROJECT,
    VALIDATOR_INFO_PATH,
    WANDB_ENTITY,
)
from natix.validator.forward import forward
from neurons.validator_proxy import ValidatorProxy

os.environ["CUDA_VISIBLE_DEVICES"] = ""


class Validator(BaseValidatorNeuron):
    """
    The Natix Validator's `forward` function sends single-image challenges to miners every 30 seconds, where each
    image has a 50/50 chance of being real or fake. In service of this task, the Validator class has two key members -
    self.real_image_datasets and self.synthetic_image_generator. The former is a list of ImageDataset objects, which
    contain real images. The latter is an ML pipeline that combines an LLM for prompt generation and diffusion
    models that ingest prompts output by the LLM to produce synthetic images.

    The Natix Validator also encapsuluates a ValidatorProxy, which is used to service organic requests from
    our consumer-facing application. If you wish to participate in this system, run your validator with the
     --proxy.port argument set to an exposed port on your machine.
    """

    def __init__(self, config=None):
        super(Validator, self).__init__(config=config)
        bt.logging.info("load_state()")
        self.load_state()

        self.last_responding_miner_uids = []
        self.validator_proxy = ValidatorProxy(self)

        # real media caches are updated by the natix_cache_updater process (started by start_validator.sh)
        self.roadwork_media_cache = {
            "image": ImageCache(ROADWORK_IMAGE_CACHE_DIR),
        }
        self.clear_road_media_cache = {
            "image": ImageCache(CLEAR_IMAGE_CACHE_DIR),
        }

        # synthetic media caches are populated by the SyntheticDataGenerator process (started by start_validator.sh)
        self.synthetic_media_cache = {
            "image": {"t2i": ImageCache(T2I_CACHE_DIR), "i2i": ImageCache(I2I_CACHE_DIR)},
        }

        self.media_cache = {
            "None": self.clear_road_media_cache,
            "Roadwork": self.roadwork_media_cache,
        }

        self.init_wandb()
        self.store_vali_info()
        self._fake_prob = self.config.get("fake_prob", 0.5)

    async def forward(self):
        """
        Validator forward pass. Consists of:
        - Generating the query
        - Querying the miners
        - Getting the responses
        - Rewarding the miners
        - Updating the scores
        """
        return await forward(self)

    def init_wandb(self):
        if self.config.wandb.off:
            return

        run_name = f"validator-{self.uid}-{natix.__version__}"
        self.config.run_name = run_name
        self.config.uid = self.uid
        self.config.hotkey = self.wallet.hotkey.ss58_address
        self.config.version = natix.__version__
        self.config.type = self.neuron_type

        wandb_project = TESTNET_WANDB_PROJECT
        if self.config.netuid == MAINNET_UID:
            wandb_project = MAINNET_WANDB_PROJECT

        # Initialize the wandb run for the single project
        bt.logging.info(f"Initializing W&B run for '{WANDB_ENTITY}/{wandb_project}'")
        try:
            run = wandb.init(
                name=run_name,
                project=wandb_project,
                entity=WANDB_ENTITY,
                config=self.config,
                resume="auto",
                tags=[self.config.neuron.name],
                dir=self.config.full_path,
                reinit=True,
            )
        except wandb.UsageError as e:
            bt.logging.warning(e)
            bt.logging.warning("Did you run wandb login?")
            return

        # Sign the run to ensure it's from the correct hotkey
        signature = self.wallet.hotkey.sign(run.id.encode()).hex()
        self.config.signature = signature
        wandb.config.update(self.config, allow_val_change=True)

        bt.logging.success(f"Started wandb run {run_name}")

    def store_vali_info(self):
        """
        Stores the uid, hotkey and netuid of the currently running vali instance.
        The SyntheticDataGenerator process reads this to name its w&b run
        """
        validator_info = {
            "uid": self.uid,
            "hotkey": self.wallet.hotkey.ss58_address,
            "netuid": self.config.netuid,
            "full_path": self.config.neuron.full_path,
        }
        with open(VALIDATOR_INFO_PATH, "w") as f:
            yaml.safe_dump(validator_info, f, indent=4)

        bt.logging.info(f"Wrote validator info to {VALIDATOR_INFO_PATH}")


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    with Validator() as validator:
        while True:
            log = (
                "Validator | "
                f"UID:{validator.uid} | "
                # f"Block:{self.current_block} | "
                f"Stake:{validator.metagraph.S[validator.uid]:.3f} | "
                f"VTrust:{validator.metagraph.Tv[validator.uid]:.3f} | "
                f"Dividend:{validator.metagraph.D[validator.uid]:.3f} | "
                f"Emission:{validator.metagraph.E[validator.uid]:.3f}"
            )
            bt.logging.info(log)
            time.sleep(30)
